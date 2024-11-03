import json
import os
from pathlib import Path
from random import Random

from calc_logs_statistics import get_log_summary_by_tasks, log_summary_to_ladder

DATA_DIR = Path('data')

def get_tasks(dataset):
    files = os.listdir(str(DATA_DIR / dataset))
    return [f.split(".")[0] for f in files]

def get_task_mix(dataset, seed=42, **groups):
    task_score_groups = get_task_score_groups(dataset)
    task_ids = []
    random_state = Random(seed)
    for k, v in groups.items():
        sample_len = min(len(task_score_groups[k]), v)
        task_ids.extend(random_state.sample(task_score_groups[k], k=sample_len))
    return task_ids
class Dataset:
    def __init__(self, dataset_location, _DATA_DIR = DATA_DIR):
        self.DATA_DIR = _DATA_DIR
        self.dataset_location = dataset_location
    def read_task(self, task_id):
        json_text = (self.DATA_DIR / self.dataset_location / f'{task_id}.json').read_text()
        return json.loads(json_text)

    def string_encode(self):
        return f"LOCAL_DATASET:{self.DATA_DIR}:{self.dataset_location}"

def loadDataset(dataset_descriptor):
    type, dr, location = dataset_descriptor.split(":")
    if type == "LOCAL_DATASET":
        return Dataset(location, Path(dr))

def score_detailed(task_id, dataset, solutions):
    if solutions is None:
        return 0
    task = dataset.read_task(task_id)
    test_input_grids = task['test']
    if isinstance(test_input_grids, dict) and 'input' in test_input_grids:
        test_input_grids = [test_input_grids]
    
    score = 0
    for pair, solution in zip(test_input_grids, solutions):
        output_grid = pair['output']
        if output_grid == solution:
            score += 1
    
    return score / len(test_input_grids)
