import os
from pathlib import Path
from random import Random

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
