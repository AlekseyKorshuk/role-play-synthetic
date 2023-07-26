from dataclasses import dataclass
from typing import List
from enum import Enum


class Role(Enum):
    USER = "user"
    CHARACTER = "character"


@dataclass
class ConversationTurn:
    role: Role
    content: str


@dataclass
class Seed:
    name: str
    categories: List[str]
    personalities: List[str]
    description: str = None
    conversation: List[ConversationTurn] = None
    is_input: bool = False

    @property
    def first_message(self):
        first_message = self.conversation[0].content
        return first_message

    @property
    def personalities_string(self):
        personalities_str = ", ".join(self.personalities)
        return personalities_str

    @property
    def categories_string(self):
        categories_str = ", ".join(self.categories)
        return categories_str

    @property
    def user_conversation_history(self):
        conversation = self.conversation
        if not self.is_input:
            conversation = _get_conversation_history_by_role(conversation, Role.USER)
        conversation_history = _conversation_to_string(conversation, self.name)
        return conversation_history

    @property
    def character_conversation_history(self):
        conversation = self.conversation
        if not self.is_input:
            conversation = _get_conversation_history_by_role(conversation, Role.CHARACTER)
        conversation_history = _conversation_to_string(conversation, self.name)
        return conversation_history

    @property
    def user_message(self):
        message = _get_last_message_by_role(self.conversation, Role.USER)
        return message

    @property
    def character_message(self):
        message = _get_last_message_by_role(self.conversation, Role.CHARACTER)
        return message

    def to_dict(self):
        dictionary = {
            "name": self.name,
            "categories": self.categories,
            "personalities": self.personalities,
            "description": self.description,
            "conversation": [
                {
                    "role": "user" if conversation_turn.role == Role.USER else "character",
                    "content": conversation_turn.content
                } for conversation_turn in self.conversation
            ]
        }
        return dictionary

    def print(self):
        print(f"Name: {self.name}")
        print(f"Categories: {self.categories_string}")
        print(f"Personalities: {self.personalities_string}")
        print(f"Description: {self.description}")
        print("Conversation:")
        for conversation_turn in self.conversation:
            role = 'You' if conversation_turn.role == Role.USER else self.name
            print(f"{role}: {conversation_turn.content}")


def _get_last_message_by_role(conversation, role):
    message_index = _get_last_message_index(conversation, role)
    message = conversation[message_index - 1].content
    return message


def _get_last_message_index(conversation, role):
    for i, turn in enumerate(conversation[::-1]):
        if turn.role == role:
            return len(conversation) - i
    return -1


def _get_conversation_history_by_role(conversation, role):
    message_index = _get_last_message_index(conversation, role)
    pre_conversation = conversation[:message_index - 1]
    return pre_conversation


def _conversation_to_string(conversation, name):
    conversation_string = ""
    for turn in conversation:
        role_name = "You"
        if turn.role == Role.CHARACTER:
            role_name = name
        conversation_string += f"{role_name}: {turn.content}\n"
    conversation_string = conversation_string.strip()
    return conversation_string


def get_empty_seed(name):
    seed = Seed(
        name=name,
        categories=[],
        personalities=[],
        description="",
        conversation=[
            ConversationTurn(role=Role.CHARACTER, content=""),
            ConversationTurn(role=Role.USER, content=""),
        ],
        is_input=True
    )
    return seed
