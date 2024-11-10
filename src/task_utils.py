import os
from pathlib import Path
from random import Random

def get_task_mix(dataset, seed=42, **groups):
    task_score_groups = get_task_score_groups(dataset)
    task_ids = []
    random_state = Random(seed)
    for k, v in groups.items():
        sample_len = min(len(task_score_groups[k]), v)
        task_ids.extend(random_state.sample(task_score_groups[k], k=sample_len))
    return task_ids


def calc_score(task_id, dataset, solutions, detailed):
    if solutions is None:
        return 0
    
    task = dataset.read_task(task_id)
    test_input_grids = task['test']
    if isinstance(test_input_grids, dict) and 'input' in test_input_grids:
        test_input_grids = [test_input_grids]
    
    if detailed:
        sum_score, tot = 0, 0
        for pair, solution in zip(test_input_grids, solutions):
            if 'output' in pair:
                tot += 1
                if pair['output'] == solution:            
                    sum_score += 1
        if tot != 0:
            return sum_score / tot
        else:
            return None
    
    else:
        has_output = False
        for pair, solution in zip(test_input_grids, solutions):
            if 'output' in pair:
                has_output = True
                if pair['output'] != solution:
                    return 0
        
        if has_output:
            return 1
        else:
            return 0
