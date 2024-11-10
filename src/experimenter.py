import json
import os
from pathlib import Path
import signal
import time
from multiprocessing import Pool
import traceback

from dataset import Dataset
from log_utils import add_item_to_big_log, add_string_to_log
from task_utils import calc_score

list_of_results = []


def solver_wrapper(args):
    solver, task_id, dataset, log_dir = args
    (log_dir / task_id).mkdir(parents=True, exist_ok=True)
    try:
        return solver(task_id, dataset, log_dir)
    except Exception as e:
        if not hasattr(e, 'ak_data'):
            e.ak_data = {}
        e.ak_data.update({'task_id': task_id, 'dataset': dataset,
            'log_file': log_dir / task_id / f'{1}.full.md', # in case of multi-runner, 1.full.md is deemed as the main log file
            'trace_back': traceback.format_exc()
        })
        raise e


# Async model is cooporative multitasking with no preemption
def _task_done(result):
    task_id, dataset, log_file, solutions = result
    results_json_file = log_file.parent.parent / 'results.json'
    termination_reason = 'timeout' if solutions is None else 'success'
    score = calc_score(task_id, dataset, solutions, detailed=False)

    add_string_to_log(f"# Termination information\n## Reason\nsuccess\n##Solutions\n{solutions}\n", log_file)
    add_string_to_log(f"##Score\nscore is {score}\n", log_file)
    print(f"Task done: {dataset=} {task_id=}, {score=}")
    add_item_to_big_log(task_id, dataset, termination_reason, score, results_json_file)
    list_of_results.append((task_id, dataset, log_file, solutions, termination_reason, score))


def _task_error(raised_exception):
    try:
        print(f'(Early exception print) {raised_exception}')
        # assert hasattr(raised_exception, 'ak_data')
        d = raised_exception.ak_data
        task_id, dataset, log_file = d['task_id'], d['dataset'], d['log_file']
        results_json_file = log_file.parent.parent / 'results.json'
        print(f'Task error: {raised_exception} ({raised_exception.ak_data})')
        add_string_to_log(f"# Termination information\n## Reason\nerror\n## Error data\n```\n{raised_exception}\n```\n## Error ak_data\n```\n{raised_exception.ak_data}\n```\n", log_file)
        add_string_to_log(f"##Score\nscore is 0.0\n", log_file)
        add_item_to_big_log(task_id, dataset, 'error', 0.0, results_json_file, raised_exception, raised_exception.ak_data)
    except:
        pass


def create_and_save_submission_file(dataset_: Dataset, list_of_results):
    submission_obj = {}
    for task_id in dataset_.get_all_task_ids():
        submission_obj[task_id] = []
        task = dataset_.read_task(task_id)
        for i in range(len(task['test'])):
            submission_obj[task_id].append({
                'attempt_1': [[0]],
                'attempt_2': [[0]]
            })

    for result in list_of_results:
        task_id, dataset, log_file, solutions, termination_reason, score = result
        if solutions:
            for i, sol in enumerate(solutions):
                submission_obj[task_id][i]['attempt_1'] = sol

    Path('submission.json').write_text(json.dumps(submission_obj))


class TimeoutException(Exception):
    pass

def handler(signum, frame):
    os.kill(os.getpid(), signal.SIGINT)
    raise TimeoutException("The model.generate() call timed out.")

def experiment(solver, task_ids, dataset, log_dir: Path, pool_size=5, timeout_seconds=None):
    """
        pool_size = -1: no multi-processing
    """
    print(f'=== Experiment started ' + '=======' * 8)
    print(f'{len(task_ids)=}')
    print(f'{pool_size=}')
    print(f'Live view: http://127.0.0.1:5000/experiment_summary#{log_dir.parent.name}-{log_dir.name}')
    print('=======' * 11 + '==\n')

    if timeout_seconds is not None:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)

    # create an empty submission file, just in case!
    create_and_save_submission_file(dataset, [])

    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / 'results.json').touch()


    all_job_args = [(solver, task_id, dataset, log_dir) for task_id in task_ids]
    
    try:
        if pool_size == -1:
            for job_args in all_job_args:
                try:
                    result = solver_wrapper(job_args)
                    _task_done(result)
                except Exception as e:
                    _task_error(e)
        else:
            with Pool(pool_size) as p:
                for job_args in all_job_args:
                    p.apply_async(
                        solver_wrapper,
                        args=(job_args,),
                        callback=_task_done,
                        error_callback=_task_error
                    )

                p.close()
                p.join()
    except:
        pass
    
    sum_scores = sum(int(e[-1] or 0) for e in list_of_results)
    print(f'\n\nExperiment finished. {len(list_of_results)=}, {sum_scores=}')
    create_and_save_submission_file(dataset, list_of_results)
    print('Submission file saved.')


