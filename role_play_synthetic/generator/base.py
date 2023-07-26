from typing import List

from role_play_synthetic.models.base import Model
from role_play_synthetic.prompters.base import Prompter
from role_play_synthetic.prompters.seed import Seed, ConversationTurn, Role


class Generator:

    def __init__(self, prompter: Prompter, model: Model):
        self.prompter = prompter
        self.model = model

    def generate(self, seeds: List[Seed], input_seed: Seed, generation_params=None):
        if generation_params is None:
            generation_params = {}
        description_prompt = self.prompter.get_description_prompt(seeds, input_seed)
        input_seed.description = self.model.generate(description_prompt, generation_params)
        first_message_prompt = self.prompter.get_first_message_prompt(seeds, input_seed)
        first_message = self.model.generate(first_message_prompt, generation_params)
        input_seed.conversation = [ConversationTurn(role=Role.CHARACTER, content=first_message)]
        input_seed = self._extend_conversation(seeds, input_seed, generation_params)
        return input_seed

    def _extend_conversation(self, seeds, input_seed, generation_params):
        for i in range(6):
            role = Role.USER if i % 2 == 0 else Role.CHARACTER
            if role == Role.USER:
                prompt = self.prompter.get_user_message_prompt(seeds, input_seed)
            else:
                prompt = self.prompter.get_character_message_prompt(seeds, input_seed)
            message = self.model.generate(prompt, generation_params)
            input_seed.conversation.append(ConversationTurn(role=role, content=message))
        return input_seed
