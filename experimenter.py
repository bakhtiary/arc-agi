import time
from multiprocessing import Pool

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

def experiment(solver, task_ids, log_dir, dataset, pool_size=5):
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Async model is cooporative multitasking with no preemption
    with open(f'{log_dir}/results.txt', 'a') as fout:
        def _task_done(result):
            list_of_results.append(result)
            log_dir, dataset, task_id, solutions = result
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

        # _task_done(solver(**{'task_id': task_ids[0], 'dataset': dataset, 'num_beams': 1, 'log_dir': log_dir, 'msg': ''}))
        
        num_tasks = len(task_ids)
        all_job_args = [(task_id, dataset, 1, log_dir, f'{task_i}/{num_tasks}')
            for task_i, task_id in enumerate(task_ids, 1)]
        with Pool(pool_size) as p:
            for job_args in all_job_args:
                # print(job_args)
                p.apply_async(
                    solver,
                    args=job_args,
                    callback=_task_done,
                    error_callback=_task_error
                )

            p.close()
            p.join()
    print(list_of_results)
