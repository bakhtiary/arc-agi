from state_machine_solver import StateMachineSolver


class StateMachineMultiSolver:
    def __init__(self, state_machine_classes):
        self.state_machine_classes = state_machine_classes

    def __call__(self, task_id, dataset, log_dir):
        last_results = None
        for i, state_machine_class in enumerate(self.state_machine_classes, 1):
            log_file = log_dir / task_id / f'{i}.full.md'
            solver = StateMachineSolver(state_machine_class)
            results = solver(task_id, dataset, log_dir, log_file)
            task_id, dataset, log_file, solution = results
            if solution is not None:
                return results
            last_results = results
        
        return last_results


class StateMachineSolverWithRestart:
    def __init__(self, state_machine_class, num_restarts=5):
        self.state_machine_class = state_machine_class
        self.num_restarts = num_restarts

    def __call__(self, task_id, dataset, log_dir):
        last_results = None
        for i in range(self.num_restarts):
            log_file = log_dir / task_id / f'{i+1}.full.md'
            solver = StateMachineSolver(self.state_machine_class)
            results = solver(task_id, dataset, log_dir, log_file)
            task_id, dataset, log_file, solution = results
            if solution is not None:
                return results
            last_results = results
        
        return last_results

