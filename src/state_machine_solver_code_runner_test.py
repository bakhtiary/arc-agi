# Run test with ```.venv/bin/python -m unittest state_machine_solver_code_runner_test.py -v```

import unittest

from state_machine_solver_code_runner import CodeRunner


class StateMachineSolverCodeRunnerTest(unittest.TestCase):

    def test_we_can_run_code_directly_from_main(self):
        code = """
def solve(input_grid):
    return [[5, 5, 5, 5, 3, 5, 5, 5, 3, 5], [1, 1, 5, 5, 5, 5, 5, 5, 5, 5], [1, 5, 5, 5, 5, 5, 1, 1, 5, 2], [5, 5, 3, 5, 5, 5, 5, 1, 5, 2], [5, 5, 5, 5, 2, 2, 5, 5, 5, 5], [2, 5, 3, 5, 5, 5, 5, 3, 5, 2], [2, 5, 5, 5, 2, 2, 5, 5, 5, 2], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [5, 5, 5, 5, 5, 5, 5, 5, 5, 2], [3, 5, 5, 5, 5, 5, 5, 3, 5, 2]]
"""
        return_value = CodeRunner().start_running(task_id="e8593010", dataset="training", code=code)

        assert "Please take your time to think about" in return_value


    # def test_we_can_run_code_in_a_separate_process(self):
    # --> ..._utils_test.test_we_can_run_code_from_chat_response

