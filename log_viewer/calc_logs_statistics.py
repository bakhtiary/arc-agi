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


def majority_of_bool_list(v):
    num_t = len([e for e in v if e])
    if num_t == len(v)/2:
        return None # tie
    return num_t > len(v) / 2
