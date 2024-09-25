from multiprocessing import Pool

from task_utils import read_task


def experiment(solver, task_ids, log_dir, dataset):
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir/'results.txt', 'w') as fout:
        def _task_done(result):
            task_id, solution = result
            task = read_task(task_id, dataset)
            fout.write(str(result))
            if task['test'][0]['output'] == solution:
                success_result = 'succeeded'
            else:
                success_result = 'failed'
            fout.write(str(success_result))
            fout.flush()
        def _task_error(raised_exception):
            print(raised_exception)

        # _task_done(solver([{'task_id': task_id, 'dataset': dataset, 'num_beams': 1, 'log_dir': log_dir} for task_id in task_ids][0]))
        with Pool(5) as p:
            for job_args in [{'task_id':task_id, 'dataset':dataset, 'num_beams':1, 'log_dir':log_dir} for task_id in task_ids ][1:]:
                p.apply_async(
                    solver,
                    kwds=job_args,
                    callback=_task_done,
                    error_callback=_task_error
                )

        p.close()
        p.join()

