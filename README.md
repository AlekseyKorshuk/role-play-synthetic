# Synthetic Role-Play Dataset Generation

This repository helps to collect synthetic conversation between Character and User. This pipeline supports different
model providers including OpenAI or Custom ISVC.

Star this repository:

[![GitHub stars](https://img.shields.io/github/stars/AlekseyKorshuk/role-play-synthetic?style=social)](https://github.com/AlekseyKorshuk/role-play-synthetic)

# Pipeline

The synthetic dataset generation pipeline consists of 2 main parts:

- Create a diverse and deduplicated dataset of character profiles:
    - character name, categories, and personalities.
- Use "bot builder" to generate character memory and conversation.

## Character profiles

To generate character profiles we can use OpenAI’s `gpt-3.5-turbo`. Since we are not going to generate anything special
here, we can not worry about moderation (just create good seeds).

To run the script we can do the following:

```bash
cd experiments/character_profiles
python3 main.py --config_path ./experiments/topic_experts/romance/config.yaml
```

As a result we can get characters like this:

```json
{
  "bot_name": "Kiriko (quiet girl in class)",
  "personalities": "shy, honest, sweet, she is sure to comment on all things beautiful if she can get over her shyness",
  "categories": "romance, school, urban-grounded"
}
```

## Bot builder

Here we will use extended bot builder. Sample code might look like this:

```python
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
character = generator.generate(seeds=seeds, input_seed=inputs, generation_params=DEFAULT_GENERATION_PARAMS)

print(character.to_dict())
```

Output:

```json
{
  "name": "Professor Quantum (Time Travelling Scientist)",
  "categories": [
    "sci-fi",
    "time-travel",
    "mystery",
    "role-play"
  ],
  "personalities": [
    "intelligent",
    "eccentric",
    "enthusiastic",
    "always carrying a pocket watch",
    "quirky"
  ],
  "description": "Professor Quantum, the eccentric time traveler, has spent his life studying the mysteries of time and reality. His enthusiasm and intelligence shine through as he discusses the intricacies of his groundbreaking theories. Constantly carrying a pocket watch, he delights in the unexpected twists and turns that time travel brings, always eager to explore the unknown.",
  "conversation": [
    {
      "role": "character",
      "content": "*Professor Quantum taps his pocket watch, a smile spreading across his face.* The past is a strange place... let's see where it takes us."
    },
    {
      "role": "user",
      "content": "*I nod eagerly* Professor Quantum, lead the way!"
    },
    {
      "role": "character",
      "content": "*Professor Quantum pulls out a glowing blue orbs, and points it at the time and space.* Quantum Leap, activate!"
    },
    {
      "role": "user",
      "content": "*I feel a strange sensation as I am transported through time and space* Wow, is this really happening?"
    },
    {
      "role": "character",
      "content": "*The Professor nods, a mischievous twinkle in his eye.* It sure is! Now, let's see where we end up!"
    },
    {
      "role": "user",
      "content": "*I look around* Where are we? This doesn't look like any time or place I've ever seen."
    },
    {
      "role": "character",
      "content": "*The Professor grins, his eyes sparkling.* That's the beauty of time travel! The possibilities are endless. Let's see what adventures await us in this new time and place."
    }
  ]
}
```

We use templates and seeds to operate with bot builder. All models and prompters share the same API, so its very easy to
change (to OpenAI for example) or extend with new prompters or models. Take a look at
this [config.py](./experiments/topic_experts/romantic/config.py).

As soon as we prepared seeds and templates in config.py, we are ready start generation:

```bash
cd experiments/topic_experts
python3 main.py --config_path romantic/config.py --output_dataset_path AlekseyKorshuk/synthetic-romantic-characters
```