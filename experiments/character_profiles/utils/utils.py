import json
import re

import yaml

NON_ALPHANUM_RE = re.compile(r"[^a-zа-яё0-9]+")


def load_yaml(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def tokenize(text):
    text = text.lower()
    text = NON_ALPHANUM_RE.sub(" ", text)
    return text.split()


def construct_openai_prompt(samples, system_task):
    messages = [{"role": "user", "content": system_task}]
    for sample in samples:
        sample.pop("most_similar_chars", None)
        sample.pop("avg_similarity_score", None)
        messages.append(
            {"role": "assistant", "content": json.dumps(sample)}
        )
    return messages


def post_process_response(response):
    if not response:
        return {}
    if response["finish_reason"] == "length":
        return {}
    raw_content = response["message"]["content"]
    try:
        char = json.loads(raw_content)
        assert "bot_name" in char.keys()
        assert "categories" in char.keys()
        assert "personalities" in char.keys()
        if isinstance(char, dict):
            return char
        else:
            return {}
    except Exception:
        return {}


def sample_to_text(sample):
    text = f"{sample['bot_name']}\n" \
           f"{sample['categories']}\n" \
           f"{sample['personalities']}\n"
    text = text.strip()
    return text


def read_jsonl(file_name):
    with open(file_name) as r:
        return [json.loads(line) for line in r]


def write_jsonl(records, path):
    with open(path, "w") as w:
        for r in records:
            w.write(json.dumps(r, ensure_ascii=False) + "\n")
