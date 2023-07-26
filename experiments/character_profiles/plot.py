import os

import click
from nomic import atlas
from utils.utils import read_jsonl, sample_to_text, load_yaml


@click.command()
@click.option("--config_path", type=str)
def main(config_path):
    config = load_yaml(config_path)
    seeds = load_character_profiles(config["seed_path"], label="initial")
    print(f"Number of seeds: {len(seeds)}")
    accepted = load_character_profiles(config["accepted_path"], label="accepted")
    print(f"Number of accepted: {len(accepted)}")
    rejected = load_character_profiles(config["rejected_path"], label="rejected")
    print(f"Number of rejected: {len(rejected)}")
    character_profiles = seeds + accepted + rejected
    print(f"Number of total: {len(character_profiles)}")
    deduplicated_character_profiles = list({v['bot_name']: v for v in character_profiles}.values())
    percentage = len(deduplicated_character_profiles) / len(character_profiles) * 100.0
    print(f"Number of deduplicated: {len(deduplicated_character_profiles)} = {percentage:.2f}%")
    breakpoint()
    character_profiles = prepare_character_profiles(deduplicated_character_profiles)
    project = atlas.map_text(
        data=character_profiles,
        indexed_field="text",
        name=f"Character Profiles: {config_path}",
        colorable_fields=["label"],
        reset_project_if_exists=True,
        duplicate_detection=True
    )

    with project.wait_for_project_lock():
        map = project.maps[0]
        print(map.duplicates)


def load_character_profiles(file_path, label):
    if not os.path.exists(file_path):
        return []
    character_profiles = read_jsonl(file_path)
    for i in range(len(character_profiles)):
        character_profiles[i]["label"] = label
        character_profiles[i]["text"] = sample_to_text(character_profiles[i])
    return character_profiles


def prepare_character_profiles(character_profiles):
    prepared_character_profiles = [
        {
            "text": sample["text"],
            "label": sample["label"]
        } for sample in character_profiles
    ]
    return prepared_character_profiles


if __name__ == "__main__":
    main()
