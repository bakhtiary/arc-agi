import time
from multiprocessing import Pool
import traceback

from log_utils import add_item_to_big_log, add_string_to_log
from task_utils import score_detailed

list_of_results = []


def solver_wrapper(args):
    print(args)
    solver, task_id, dataset, log_dir = args
    try:
        return solver(task_id, dataset, log_dir)
    except Exception as e:
        error_msg = traceback.format_exc()
        e = Exception(error_msg)
        e.ak_data = {'task_id': task_id, 'dataset': dataset,
                     'log_file': log_dir / task_id / f'{1}.full.md'}
        raise e


# Async model is cooporative multitasking with no preemption
def _task_done(result):
    list_of_results.append(result)
    task_id, dataset, log_file, solutions = result
    results_json_file = log_file.parent.parent / 'results.json'
    termination_reason = 'timeout' if solutions is None else 'success'
    score = score_detailed(task_id, dataset, solutions)

    add_string_to_log(f"# Termination information\n## Reason\nsuccess\n##Solutions\n{solutions}\n", log_file)
    add_string_to_log(f"##Score\nscore is {score}\n", log_file)
    print(f"Task done: {dataset=} {task_id=}, {score=}")
    add_item_to_big_log(task_id, dataset, termination_reason, score, results_json_file)


def _task_error(raised_exception):
    print("(Early exception print)"+str(raised_exception))
    assert hasattr(raised_exception, 'ak_data')
    d = raised_exception.ak_data
    task_id, dataset, log_file = d['task_id'], d['dataset'], d['log_file']
    results_json_file = log_file.parent.parent / 'results.json'
    print(f'Task error: {raised_exception} ({raised_exception.ak_data})')
    add_string_to_log(f"# Termination information\n## Reason\nerror\n## Error data\n{raised_exception}\n## Error ak_data\n{raised_exception.ak_data}\n", log_file)
    add_string_to_log(f"##Score\nscore is 0.0\n", log_file)
    add_item_to_big_log(task_id, dataset, 'error', 0.0, results_json_file, raised_exception, raised_exception.ak_data)

def experiment(solver, task_ids, dataset, log_dir, pool_size=5):
    """
        pool_size = -1: no multi-processing
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    all_job_args = [(solver, task_id, dataset, log_dir) for task_id in task_ids]
    
    if pool_size == -1:
        for job_args in all_job_args:
            try:
                result = solver_wrapper(job_args)
                _task_done(result)
            except Exception as e:
                _task_error(e)
    else:
        with Pool(pool_size) as p:
            p.map_async(
                solver_wrapper,
                iterable=all_job_args,
                callback=_task_done,
                error_callback=_task_error
            )

            p.close()
            p.join()
    print(list_of_results)


