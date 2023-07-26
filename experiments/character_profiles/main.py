import json
import os
import random
import shutil
import time
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from queue import Queue
from threading import Thread, Event
from typing import List, Any, Dict

import click
from datasets import Dataset, DatasetDict
import tqdm
from rouge_score import rouge_scorer

from utils import utils
from utils.openai_utils import openai_batch_completion, OpenAIDecodingArguments

# Constants
OPENAI_KEYS = os.getenv("OPENAI_KEYS", "").split(",")
SEED_SAMPLE_COUNT = 1
MACHINE_SAMPLE_COUNT = 1
TOTAL_SAMPLE_COUNT = 2
SLEEP_TIME = 1

assert len(OPENAI_KEYS) > 0


@click.command()
@click.option("--config_path", type=str)
def generate_samples(config_path: str):
    """Entry point for the CLI."""
    config = utils.load_yaml(config_path)
    run_sample_generation(config)
    push_to_hub(config)


def run_sample_generation(config: Dict[str, Any]):
    """Runs the sample generation process based on the configuration."""
    seed_samples = load_samples(config["seed_path"])
    print(f"Loaded {len(seed_samples)} seed samples.")

    machine_samples = load_samples(config["accepted_path"])
    print(f"Loaded {len(machine_samples)} machine-generated samples.")

    all_descriptions = [utils.sample_to_text(sample) for sample in seed_samples + machine_samples]
    all_description_tokens = [utils.tokenize(description) for description in all_descriptions]

    progress_bar = tqdm.tqdm(total=config["num_samples_to_generate"])
    if machine_samples:
        progress_bar.update(len(machine_samples))

    queue = Queue(0)
    stop_event = Event()

    core_args = CoreArgs(
        stop_event=stop_event,
        queue=queue,
        seed_samples=seed_samples,
        machine_samples=machine_samples,
        output_path=config["accepted_path"],
        rejected_output_path=config["rejected_path"],
        rouge_cutoff=config["rouge_cutoff"],
        all_descriptions=all_descriptions,
        all_description_tokens=all_description_tokens,
        num_cpus=config["num_cpus"],
        progress_bar=progress_bar
    )

    core = Core(core_args)
    core.start()

    workers = create_workers(config, stop_event, queue, seed_samples, machine_samples)

    while not stop_event.is_set():
        time.sleep(SLEEP_TIME)

    for worker in workers:
        worker.join()

    core.join()


@dataclass
class CoreArgs:
    stop_event: Event
    queue: Queue
    seed_samples: List[Any]
    machine_samples: List[Any]
    output_path: str
    rejected_output_path: str
    rouge_cutoff: float
    all_descriptions: List[str]
    all_description_tokens: List[List[str]]
    num_cpus: int
    progress_bar: Any  # actual type would be tqdm.tqdm, but we can't import it here


@dataclass
class WorkerArgs:
    stop_event: Event
    queue: Queue
    seed_samples: List[Any]
    machine_samples: List[Any]
    decoding_args: Any  # actual type would be OpenAIDecodingArguments, but we can't import it here
    model_name: str
    request_batch_size: int
    system_prompt: str


class Core(Thread):
    def __init__(self, args: CoreArgs):
        Thread.__init__(self)
        self.args = args
        self.rejected_samples = []

    def run(self):
        while not self.args.stop_event.is_set():
            if not self.args.queue.empty():
                self.process_sample()
            else:
                time.sleep(SLEEP_TIME)

    def process_sample(self):
        new_sample = self.args.queue.get()
        new_description_tokens = utils.tokenize(utils.sample_to_text(new_sample))
        rouge_scores = self.calculate_rouge_scores(new_description_tokens)

        if max(rouge_scores) > self.args.rouge_cutoff:
            print(f"Rejected with {max(rouge_scores)} max rogue score.")
            self.reject_sample(new_sample)
        else:
            self.accept_sample(new_sample, new_description_tokens)

    def calculate_rouge_scores(self, new_description_tokens):
        with Pool(self.args.num_cpus) as p:
            rouge_scores = p.map(
                partial(rouge_scorer._score_lcs, new_description_tokens),
                self.args.all_description_tokens,
            )
        rouge_scores = [score.fmeasure for score in rouge_scores]
        return rouge_scores

    def reject_sample(self, new_sample):
        self.rejected_samples.append(new_sample)
        if self.rejected_samples:  # Periodically write rejected samples to file
            self._write_rejected_samples()

    def accept_sample(self, new_sample, new_description_tokens):
        self.args.machine_samples.append(new_sample)
        self.args.all_descriptions.append(utils.sample_to_text(new_sample))
        self.args.all_description_tokens.append(new_description_tokens)
        self.args.progress_bar.update(1)

        utils.write_jsonl(self.args.machine_samples, self.args.output_path + "_tmp")
        shutil.move(self.args.output_path + "_tmp", self.args.output_path)

        if self.args.progress_bar.n >= self.args.progress_bar.total:
            self.args.stop_event.set()

    def _write_rejected_samples(self):
        with open(self.args.rejected_output_path, "a") as file:
            for sample in self.rejected_samples:
                file.write(json.dumps(sample) + "\n")
        self.rejected_samples = []

    def join(self):
        Thread.join(self)
        if self.rejected_samples:  # Make sure to write any remaining rejected samples
            self._write_rejected_samples()


class Worker(Thread):
    def __init__(self, args: WorkerArgs):
        Thread.__init__(self)
        self.args = args

    def run(self):
        while not self.args.stop_event.is_set():
            self.process_batch()

    def process_batch(self):
        batch = []
        for _ in range(self.args.request_batch_size):
            prompt_samples = self.get_prompt_samples()
            random.shuffle(prompt_samples)

            messages = utils.construct_openai_prompt(prompt_samples, self.args.system_prompt)
            batch.append(messages)

        self.process_results(batch)

    def get_prompt_samples(self):
        if len(self.args.machine_samples) > MACHINE_SAMPLE_COUNT:
            prompt_samples = random.sample(self.args.seed_samples, SEED_SAMPLE_COUNT) + \
                             random.sample(self.args.machine_samples, MACHINE_SAMPLE_COUNT)
        else:
            prompt_samples = random.sample(self.args.seed_samples, TOTAL_SAMPLE_COUNT)
        return prompt_samples

    def process_results(self, batch):
        results = openai_batch_completion(
            batch=batch,
            model_name=self.args.model_name,
            decoding_args=self.args.decoding_args
        )
        for result in results:
            new_sample = utils.post_process_response(result)
            if new_sample != {}:
                self.args.queue.put(new_sample)


def load_samples(path: str) -> List[Dict[str, Any]]:
    """Loads samples from a jsonl file."""
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in open(path, "r")]


def create_workers(config: Dict[str, Any], stop_event: Event, queue: Queue,
                   seed_samples: List[Dict[str, Any]], machine_samples: List[Dict[str, Any]]) -> List[Worker]:
    """Creates and starts worker threads based on the configuration."""
    workers = []
    for key in OPENAI_KEYS:
        decoding_args = OpenAIDecodingArguments(
            **config["openai_generation_params"],
            api_key=key
        )
        worker_args = WorkerArgs(
            stop_event=stop_event,
            queue=queue,
            seed_samples=seed_samples,
            machine_samples=machine_samples,
            decoding_args=decoding_args,
            model_name=config["model_name"],
            request_batch_size=config["request_batch_size"],
            system_prompt=config["system_prompt"]
        )
        worker = Worker(worker_args)
        worker.start()
        workers.append(worker)
    return workers


def push_to_hub(config):
    seeds = utils.read_jsonl(config["seed_path"])
    accepted = utils.read_jsonl(config["accepted_path"])
    rejected = utils.read_jsonl(config["rejected_path"])

    dataset = DatasetDict(
        {
            "seeds": Dataset.from_list(seeds),
            "accepted": Dataset.from_list(accepted),
            "rejected": Dataset.from_list(rejected),
        }
    )
    dataset.push_to_hub(config["dataset_path"], private=True)


if __name__ == "__main__":
    generate_samples()
