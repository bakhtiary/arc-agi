import time
from multiprocessing import Pool

from task_utils import read_task

list_of_results = []
def _task_done(result):
    list_of_results.append(result)
    print(f"task done {result}")
    log_dir, dataset, task_id, solution = result
    with open(f'{log_dir}/results.txt', 'a') as fout:
        task = read_task(task_id, dataset)
        fout.write(str(result))
        expected_solution = task['test'][0]['output']
        if expected_solution == solution:
            success_result = ' succeeded\n'
        else:
            success_result = f' failed, we were expecting this solution: {expected_solution} \n'
        fout.write(str(success_result))
        fout.flush()


def _task_error(raised_exception):
    print(raised_exception)


def experiment(solver, task_ids, log_dir, dataset):
    log_dir.mkdir(parents=True, exist_ok=True)

    _task_done(solver(**{'task_id': task_ids[0], 'dataset': dataset, 'num_beams': 1, 'log_dir': str(log_dir)}))
    with Pool(5) as p:
        for job_args in [(task_id, dataset, 1, str(log_dir)) for task_id in task_ids ]:
            print(job_args)
            p.apply_async(
                solver,
                args=job_args,
                callback=_task_done,
                # error_callback=_task_error
            )

    p.close()
    p.join()
    print(list_of_results)
