from role_play_synthetic.prompters.base import Prompter


class OpenAIPrompter(Prompter):

    def get_description_prompt(self, seeds, inputs):
        prompt = _get_openai_conversation(seeds, inputs, self.description_template)
        return prompt

    def get_first_message_prompt(self, seeds, inputs):
        prompt = _get_openai_conversation(seeds, inputs, self.first_message_template)
        return prompt

    def get_user_message_prompt(self, seeds, inputs):
        prompt = _get_openai_conversation(seeds, inputs, self.user_message_template)
        return prompt

    def get_character_message_prompt(self, seeds, inputs):
        prompt = _get_openai_conversation(seeds, inputs, self.character_message_template)
        return prompt


def _get_openai_conversation(seeds, inputs, template):
    conversation = [{"role": "system", "content": template.system_message}]
    for seed in seeds:
        user_content = template.user_template.format(seed=seed)
        assistant_content = template.assistant_template.format(seed=seed)
        conversation.extend(
            [{"role": "user", "content": user_content}, {"role": "assistant", "content": assistant_content}]
        )
    user_input = template.user_template.format(seed=inputs)
    conversation.append(
        {"role": "user", "content": user_input}
    )
    return conversation
