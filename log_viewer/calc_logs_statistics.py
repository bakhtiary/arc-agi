from collections import defaultdict
from pathlib import Path
try:
    from log_utils import read_jsonl
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from log_utils import read_jsonl

def get_log_summaries(root_dir='important-run-logs'):
    log_summary = defaultdict(lambda: defaultdict(lambda: (0,0,0)))
    for i, results_json in enumerate(Path(root_dir).rglob('results.json')):
        objs = read_jsonl(results_json)
        for obj in objs:
            count, score, tot = log_summary[obj['dataset']][obj['task_id']]
            log_summary[obj['dataset']][obj['task_id']] = (count + 1, score + obj['score'], i)
    return log_summary

def log_summary_to_ladder(log_summary):
    ladder = defaultdict(lambda: defaultdict(list))
    for dataset, rest in log_summary.items():
        for task_id, tup in rest.items():
            count, score, tot = tup
            ladder[dataset][score].append(task_id)
        ladder[dataset] = dict(sorted(ladder[dataset].items()))
    return ladder

    
if __name__ == '__main__':
    log_summary = get_log_summaries()
    ladder = log_summary_to_ladder(log_summary)
    for dataset, rest in ladder.items():
        for score, task_ids in rest.items():
            print(dataset, score, len(task_ids))
    