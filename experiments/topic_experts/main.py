import os.path
from typing import Dict, Any
import hashlib
import json
import importlib
from queue import Queue
from threading import Thread, Event

import click
import tqdm
from datasets import load_dataset, Dataset

from role_play_synthetic.generator.base import Generator
from role_play_synthetic.models.chai_isvc import ChaiISVCModel
from role_play_synthetic.prompters.vicuna_v1 import VicunaV1Prompter
from role_play_synthetic.prompters.seed import Seed

ENDPOINT_URL = os.getenv("ENDPOINT_URL")

DEFAULT_GENERATION_PARAMS = {
    'temperature': 0.9,
    'top_p': 1,
    'top_k': 40,
    'frequency_penalty': 0.,
    'presence_penalty': 0.1,
    'max_new_tokens': 256
}


@click.command()
@click.option("--config_path", type=str)
@click.option("--output_dataset_path", type=str)
def main(config_path, output_dataset_path):
    config_path = config_path.replace("/", ".").replace(".py", "")
    config = importlib.import_module(config_path)
    save_directory = "/".join(config_path.replace(".", "/").split("/")[:-1])
    save_directory = f"./{save_directory}/characters"
    if not os.path.exists(save_directory):
        os.mkdir(save_directory)
    dataset = load_dataset(config.dataset_path, split="train")

    queue = Queue(0)
    for sample in dataset:
        queue.put(sample)

    progress_bar = tqdm.tqdm(total=len(dataset))

    workers = []
    for _ in range(config.num_workers):
        worker = Worker(config, queue, save_directory, progress_bar)
        worker.start()
        workers.append(worker)

    for worker in workers:
        worker.join()

    characters = load_saved_characters(save_directory)
    ds = Dataset.from_list(characters)
    ds.push_to_hub(output_dataset_path, private=True)


def get_dictionary_hash(dictionary):
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


def get_generator(config):
    model = ChaiISVCModel(endpoint_url=ENDPOINT_URL)
    prompter = VicunaV1Prompter(
        description_template=config.description_template,
        first_message_template=config.first_message_template,
        user_message_template=config.user_message_template,
        character_message_template=config.character_message_template,
    )
    generator = Generator(prompter=prompter, model=model)
    return generator


def get_input_seed_from_sample(sample):
    input_seed = Seed(
        name=sample["bot_name"],
        categories=sample["categories"].split(", "),
        personalities=sample["personalities"].split(", "),
        is_input=True
    )
    return input_seed


def load_saved_characters(save_directory):
    characters = []
    saved_characters_path = [f for f in os.listdir(save_directory) if os.path.isfile(os.path.join(save_directory, f))]
    for character_path in saved_characters_path:
        character_path = os.path.join(save_directory, character_path)
        with open(character_path) as f:
            character = json.load(f)
        characters.append(character)
    return characters


class Worker(Thread):
    def __init__(self, config, queue, save_directory, progress_bar):
        Thread.__init__(self)
        self.config = config
        self.queue = queue
        self.save_directory = save_directory
        self.progress_bar = progress_bar
        self.generator = get_generator(config)

    def run(self):
        while not self.queue.empty():
            sample = self.queue.get()
            sample_hash = get_dictionary_hash(sample)
            file_path = f"{self.save_directory}/{sample_hash}.json"
            if os.path.exists(file_path):
                self.progress_bar.update(1)
                continue
            input_seed = get_input_seed_from_sample(sample)
            try:
                character = self.generator.generate(seeds=self.config.seeds, input_seed=input_seed,
                                                    generation_params=DEFAULT_GENERATION_PARAMS)
            except Exception as ex:
                print(ex)
                print(sample)
                print(sample_hash)
                continue
            with open(file_path, "w") as f:
                json.dump(character.to_dict(), f)
            self.progress_bar.update(1)


if __name__ == "__main__":
    main()
