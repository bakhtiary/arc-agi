import time
from multiprocessing import Pool
import traceback

from log_utils import add_termination_to_log, add_string_to_log
from task_utils import read_task

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
                     'log_file': log_dir / task_id / f'{1}.json'}
        raise e


# Async model is cooporative multitasking with no preemption
def _task_done(result):
    list_of_results.append(result)
    task_id, dataset, log_file, solutions = result
    score = score_detailed(task_id, dataset, solutions)
    add_string_to_log(f"score is {score}", log_file)
    print(f"Task done: {dataset=} {task_id=}, {score=}")


def _task_error(raised_exception):
    print("hello"+str(raised_exception))
    assert hasattr(raised_exception, 'ak_data')
    print(f'Task error: {raised_exception} ({raised_exception.ak_data})')
    add_termination_to_log({'termination': {'reason': 'exception', 'details': raised_exception}},
                           raised_exception.ak_data['log_file'])


def score_detailed(task_id, dataset, solutions):
    if solutions is None:
        return 0
    task = read_task(task_id, dataset)
    test_input_grids = task['test']
    if isinstance(test_input_grids, dict) and 'input' in test_input_grids:
        test_input_grids = [test_input_grids]
    
    score = 0
    for pair, solution in zip(test_input_grids, solutions):
        output_grid = pair['output']
        if output_grid == solution:
            score += 1
    
    return score / len(test_input_grids)

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


