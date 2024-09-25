import json
from pathlib import Path


def read_task(task_id, dataset):
    json_text = (Path("data") / dataset / f'{task_id}.json').read_text()
    return json.loads(json_text)
