from role_play_synthetic.prompters.openai import OpenAIPrompter
from role_play_synthetic.prompters.seed import Seed
from experiments.baseline.config import (
    seeds,
    description_template,
    first_message_template,
    user_message_template,
    character_message_template
)
from role_play_synthetic.generator.base import Generator
from role_play_synthetic.models.openai_model import OpenAIModel
import openai

openai.api_key = "<TOKEN>"
model = OpenAIModel(model_name="gpt-4")

openai_generation_params = {
    "temperature": 1.0,
    "top_p": 1.0,
    "n": 1,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}

prompter = OpenAIPrompter(
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

character = generator.generate(seeds=seeds, input_seed=inputs, generation_params=openai_generation_params)
print(character)
print(character.to_dict())
character.print()
