from collections import defaultdict
import os
from pathlib import Path
import re

def parse_logs(dataset):
    task_scores = defaultdict(list)
    root_dir = 'important-run-logs'
    if dataset == 'both':
        pattern = rf"Task done: dataset='{dataset}' task_id='([^']*)', score=([0-9.]+)"
    else:
        pattern = rf"Task done: dataset='.*' task_id='([^']*)', score=([0-9.]+)"

    for dir in os.listdir(root_dir):
        file_path = Path(root_dir) / dir / 'results.txt'
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                match = re.match(pattern, line)
                if match:
                    task_id = match.group(1)
                    score_str = match.group(2)
                    try:
                        score_value = bool(float(score_str))
                    except ValueError:
                        continue
                    task_scores[task_id].append(score_value)
    return task_scores

def majority_of_bool_list(v):
    num_t = len([e for e in v if e])
    if num_t == len(v)/2:
        return None # tie
    return num_t > len(v) / 2
    
def get_task_score_groups(dataset):
    task_scores = parse_logs(dataset)
    task_score_groups = dict()
    task_score_groups['simple'] = [k for k,v in task_scores.items()
        if len(v) >= 2 and majority_of_bool_list(v)]
    # solved only in one run, and not present in the other
    task_score_groups['simple~'] = [k for k,v in task_scores.items() 
        if len(v) == 1 and v[0]]
    task_score_groups['average'] = [k for k,v in task_scores.items()
        if len(v) >= 2 and majority_of_bool_list(v) is None]
    task_score_groups['hard'] = [k for k,v in task_scores.items()
        if len(v) >= 2 and majority_of_bool_list(v) is False]
    # not solved only in one run, and not present in the other
    task_score_groups['hard~'] = [k for k,v in task_scores.items()
        if len(v) == 1 and not v[0]]
    return task_score_groups
    
if __name__ == '__main__':
    task_score_groups = get_task_score_groups('training')
    print({k:len(v) for k,v in task_score_groups.items()})
    # print(task_score_groups)
    