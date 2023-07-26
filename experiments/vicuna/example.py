import os

from role_play_synthetic.generator.base import Generator
from role_play_synthetic.models.chai_isvc import ChaiISVCModel
from role_play_synthetic.prompters.vicuna_v1 import VicunaV1Prompter
from role_play_synthetic.prompters.seed import Seed
from experiments.vicuna.config import (
    seeds,
    description_template,
    first_message_template,
    user_message_template,
    character_message_template,
)
import time

ENDPOINT_URL = os.getenv("ENDPOINT_URL")

DEFAULT_GENERATION_PARAMS = {
    'temperature': 0.9,
    'top_p': 1,
    'top_k': 40,
    'frequency_penalty': 0.,
    'presence_penalty': 0.1
}

model = ChaiISVCModel(endpoint_url=ENDPOINT_URL)

prompter = VicunaV1Prompter(
    description_template=description_template,
    first_message_template=first_message_template,
    user_message_template=user_message_template,
    character_message_template=character_message_template,
)
generator = Generator(prompter=prompter, model=model)

inputs = Seed(
    name="Professor Quantum (Time Travelling Scientist)",
    categories=['sci-fi', 'time-travel', 'mystery', 'role-play'],
    personalities=['intelligent', 'eccentric', 'enthusiastic', 'always carrying a pocket watch', 'quirky'],
    is_input=True
)
start_time = time.time()
character = generator.generate(seeds=seeds, input_seed=inputs, generation_params=DEFAULT_GENERATION_PARAMS)
print(f"Done in {time.time() - start_time:.2f} seconds")
print(character)
print(character.to_dict())
character.print()
