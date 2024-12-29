import json
import random

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

file_path = '/bjzhyai03/workhome/lvbohan/divgpt/diverse_answers_32.jsonl'
jsonl_data = read_jsonl(file_path)

SPEC_START = "<|reserved_special_token_0|>"
SPEC_END = "<|reserved_special_token_1|>"

train = []

for d in jsonl_data:
    for a in d["diverse_responses"][:16]:
        train.append({
            "messages": [
            {
                "role": "user",
                "content": f"{SPEC_START}<|reserved_special_token_{str(random.randint(2, 250))}|>{SPEC_END}{d['query']}"
            },
            {
                "role": "assistant",
                "content": a
            }
            ]
        })

with open("train1.json", "w") as f:
    f.write(json.dumps(train, indent = 4))