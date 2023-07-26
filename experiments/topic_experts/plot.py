import click
from nomic import atlas
from datasets import load_dataset


@click.command()
@click.option("--dataset_path", type=str)
def main(dataset_path):
    dataset = load_dataset(dataset_path, split="train")
    dataset = dataset.map(prepare_sample)

    project = atlas.map_text(
        data=dataset.to_list(),
        indexed_field="text",
        name=f"Characters: {dataset_path}",
        reset_project_if_exists=True,
        duplicate_detection=True
    )

    with project.wait_for_project_lock():
        map = project.maps[0]
        print(map.duplicates)


def prepare_sample(sample):
    return {
        "categories": ", ".join(sample["categories"]),
        "personalities": ", ".join(sample["personalities"]),
        "conversation": get_text_conversation(sample),
        "text": sample_to_text(sample),
    }


def sample_to_text(sample):
    text = "Name: " + sample["name"] + "\n"
    text += "Categories: " + ", ".join(sample["categories"]) + "\n"
    text += "Personalities: " + ", ".join(sample["personalities"]) + "\n"
    text += "Description: " + sample["description"] + "\n"
    text += "Conversation:\n" + get_text_conversation(sample)
    return text


def get_text_conversation(sample):
    text = ""
    for conversation_turn in sample["conversation"]:
        role = 'You' if conversation_turn["role"] == "user" else sample["name"]
        text += f'{role}: {conversation_turn["content"]}\n'
    return text


if __name__ == "__main__":
    main()
