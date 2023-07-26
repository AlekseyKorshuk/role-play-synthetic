from dataclasses import dataclass
from typing import List

from role_play_synthetic.prompters.seed import Seed


@dataclass
class Template:
    system_message: str
    user_template: str
    assistant_template: str


class Prompter:
    def __init__(self,
                 description_template: Template,
                 first_message_template: Template,
                 user_message_template: Template,
                 character_message_template: Template):
        self.description_template = description_template
        self.first_message_template = first_message_template
        self.user_message_template = user_message_template
        self.character_message_template = character_message_template

    def get_description_prompt(self, seeds: List[Seed], inputs: Seed):
        raise NotImplemented

    def get_first_message_prompt(self, seeds: List[Seed], inputs: Seed):
        raise NotImplemented

    def get_user_message_prompt(self, seeds: List[Seed], inputs: Seed):
        raise NotImplemented

    def get_character_message_prompt(self, seeds: List[Seed], inputs: Seed):
        raise NotImplemented
