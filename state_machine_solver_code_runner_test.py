import unittest

from state_machine_solver_code_runner import Runner


class StateMachineSolverCodeRunnerTest(unittest.TestCase):

    def test_we_can_run_code_directly_from_main(self):
        code = """
def solve(input_grid):
    return [[5, 5, 5, 5, 3, 5, 5, 5, 3, 5], [1, 1, 5, 5, 5, 5, 5, 5, 5, 5], [1, 5, 5, 5, 5, 5, 1, 1, 5, 2], [5, 5, 3, 5, 5, 5, 5, 1, 5, 2], [5, 5, 5, 5, 2, 2, 5, 5, 5, 5], [2, 5, 3, 5, 5, 5, 5, 3, 5, 2], [2, 5, 5, 5, 2, 2, 5, 5, 5, 2], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [5, 5, 5, 5, 5, 5, 5, 5, 5, 2], [3, 5, 5, 5, 5, 5, 5, 3, 5, 2]]
"""
        return_value = Runner().start_running(dataset="training", task_id="e8593010", code=code)

        assert "Please take your time to think about" in return_value
