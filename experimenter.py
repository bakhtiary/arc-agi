import time
from multiprocessing import Pool
import traceback

from task_utils import read_task

list_of_results = []


def score_detailed(task_id, dataset, solutions):
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

    def solver_wrapper(args):
        try:
            solver(*args)
        except Exception as e:
            print('hi')
            error_msg = traceback.format_exc()
            e = Exception(error_msg)
            e.ak_data = {'task_id': args[0], 'dataset': args[1]}
            raise e
    
    # Async model is cooporative multitasking with no preemption
    with open(f'{log_dir}/results.txt', 'a') as fout:
        def _task_done(result):
            list_of_results.append(result)
            task_id, dataset, log_dir, solutions = result
            score = score_detailed(task_id, dataset, solutions)
            print(f"Task done: {dataset=} {task_id=}, {score=}")
            fout.write(f"Task done: {dataset=} {task_id=}, {score=}\n")
            fout.flush()

        def _task_error(raised_exception):
            if hasattr(raised_exception, 'ak_data'):
                print(f'Task error: {raised_exception} ({raised_exception.ak_data})')
                fout.write(f'Task error: {raised_exception} ({raised_exception.ak_data})\n')
            else:
                print(f'Task error: {raised_exception}')
                fout.write(f'Task error: {raised_exception}\n')

        num_tasks = len(task_ids)
        all_job_args = [(task_id, dataset, log_dir, 1, f'{task_i}/{num_tasks}')
            for task_i, task_id in enumerate(task_ids, 1)]
        
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
                    # print(job_args)
                    p.apply_async(
                        solver_wrapper,
                        args=job_args,
                        callback=_task_done,
                        error_callback=_task_error
                    )

                p.close()
                p.join()
    print(list_of_results)
