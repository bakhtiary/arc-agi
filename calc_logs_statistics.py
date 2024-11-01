from collections import defaultdict
from pathlib import Path

from log_utils import read_jsonl

def get_log_summary_by_experiments(log_root_dirs: list[Path]):
    log_summary = defaultdict(lambda: defaultdict(list)) # log_id --> reason --> [task_id]
    log_ids = set()
    for root_dir in log_root_dirs:
        for results_json in root_dir.rglob('results.json'):
            objs = read_jsonl(results_json)
            log_id = results_json.parent.name
            log_summary[log_id]
            if log_id in log_ids:
                print(f'log {log_id} already processes, deemed as redundant.')
                continue
            log_ids.add(log_id)
            for obj in objs:
                tr = obj['termination_reason']
                if tr == 'success':
                    if obj['score'] == 0:
                        tr += '_nok'
                    else:
                        tr += '_ok'
                log_summary[log_id][tr].append(obj['task_id'])
    return dict(sorted(log_summary.items()))

def get_log_summary_by_tasks(log_root_dirs: list[Path]):
    # Returns log_summary, which is: dataset --> task_id --> [(root_dir, log_id, score)]
    log_summary = defaultdict(lambda: defaultdict(list))
    log_ids = set()
    for root_dir in log_root_dirs:
        for results_json in root_dir.rglob('results.json'):
            objs = read_jsonl(results_json)
            log_id = results_json.parent.name
            if log_id in log_ids:
                print(f'log {log_id} already processes, deemed as redundant.')
                continue
            log_ids.add(log_id)
            for obj in objs:
                log_summary[obj['dataset']][obj['task_id']].append((root_dir, log_id, obj['score']))
        return log_summary

def log_summary_to_ladder(log_summary):
    # Returns ladder, which is: dataset --> sum_score --> task_id --> [(root_dir, log_id, score)]
    ladder = defaultdict(lambda: defaultdict(lambda: dict()))
    for dataset, rest in log_summary.items():
        for task_id, tups in rest.items():
            sum_score = sum(score for root_dir, log_id, score in tups)
            ladder[dataset][sum_score][task_id] = tups
        ladder[dataset] = dict(sorted(ladder[dataset].items(), reverse=True))
    return ladder

    
if __name__ == '__main__':
    log_summary_root_dirs = [Path('important-run-logs'), Path('logs')]
    log_summary = get_log_summary_by_tasks(log_summary_root_dirs)
    log_ladder = log_summary_to_ladder(log_summary)
    for dataset, rest in log_ladder.items():
        for score, task_ids in rest.items():
            print(dataset, score, len(task_ids))
    