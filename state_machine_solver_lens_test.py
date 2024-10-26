# Run test with ```.venv/bin/python -m unittest state_machine_solver_code_runner_test.py -v```

import unittest

from state_machine_solver_lens_runner import LensRunner


class StateMachineSolverLensRunnerTest(unittest.TestCase):

    def test_we_can_run_code_directly_from_main(self):
        code = """
def grid_height(input_grid):
    return len(input_grid)

"""
        return_value = LensRunner(task_id="e8593010", dataset="training", code=code).start_running()

        assert """running grid_height on input 1 and the result is 10
running grid_height on input 1 and the result is 10
running grid_height on input 2 and the result is 10
running grid_height on input 2 and the result is 10
running grid_height on input 3 and the result is 10
running grid_height on input 3 and the result is 10""" == return_value


    def test_we_can_run_two_functions(self):
        code = """
def grid_height(input_grid):
    return len(input_grid)

def return_100(input_grid):
    return 100
"""
        return_value = LensRunner(task_id="e8593010", dataset="training", code=code).start_running()

        assert "grid_height" in return_value
        assert "return_100" in return_value

    def test_we_can_handle_error_correctly(self):
        code = """
def grid_height(input_grid):
    return len(input_grid)

def grid_error(input_grid, error):
    return len(input_grid)

"""
        return_value = LensRunner(task_id="e8593010", dataset="training", code=code).start_running()

        assert "grid_height" in return_value
        assert "missing 1 required positional argument: 'error'" in return_value

