from role_play_synthetic.prompters.base import Prompter
from role_play_synthetic.prompters.seed import get_empty_seed


class VicunaV1Prompter(Prompter):

    def get_description_prompt(self, seeds, inputs):
        prompt = _get_vicuna_prompt(seeds, inputs, self.description_template)
        return prompt

    def get_first_message_prompt(self, seeds, inputs):
        prompt = _get_vicuna_prompt(seeds, inputs, self.first_message_template)
        return prompt

    def get_user_message_prompt(self, seeds, inputs):
        prompt = _get_vicuna_prompt(seeds, inputs, self.user_message_template)
        return prompt

    def get_character_message_prompt(self, seeds, inputs):
        prompt = _get_vicuna_prompt(seeds, inputs, self.character_message_template)
        return prompt


def _get_vicuna_prompt(seeds, inputs, template):
    prompt = template.system_message
    for seed in seeds:
        user_content = template.user_template.format(seed=seed)
        assistant_content = template.assistant_template.replace("*", "").format(seed=seed)
        prompt += f"\n\n### User:\n" \
                  f"{user_content}\n" \
                  f"### Assistant:\n" \
                  f"{assistant_content}"
    user_input = template.user_template.format(seed=inputs)
    assistant_content = template.assistant_template.format(seed=get_empty_seed(inputs.name))
    prompt += f"\n\n### User:\n" \
              f"{user_input}\n" \
              f"### Assistant:\n" \
              f"{assistant_content}"
    return prompt
