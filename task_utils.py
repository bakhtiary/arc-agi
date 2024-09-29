import json
import os
from pathlib import Path

DATA_DIR = Path('data')

def get_tasks(dataset):
    files = os.listdir(str(DATA_DIR / dataset))
    return [f.split(".")[0] for f in files]

def read_task(task_id, dataset):
    json_text = (DATA_DIR / dataset / f'{task_id}.json').read_text()
    return json.loads(json_text)
