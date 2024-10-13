import unittest

from state_machine_solver_utils import extract_and_run_mapping_code


class StateMachineSolverUtilsTest(unittest.TestCase):

    def test_we_can_run_code_from_chat_response(self):
        response = """
some random text
    
```python
def solve(input_grid):
    return [[5, 5, 5, 5, 3, 5, 5, 5, 3, 5], [1, 1, 5, 5, 5, 5, 5, 5, 5, 5], [1, 5, 5, 5, 5, 5, 1, 1, 5, 2], [5, 5, 3, 5, 5, 5, 5, 1, 5, 2], [5, 5, 5, 5, 2, 2, 5, 5, 5, 5], [2, 5, 3, 5, 5, 5, 5, 3, 5, 2], [2, 5, 5, 5, 2, 2, 5, 5, 5, 2], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [5, 5, 5, 5, 5, 5, 5, 5, 5, 2], [3, 5, 5, 5, 5, 5, 5, 3, 5, 2]]
```

some more random text        
"""
        return_value = extract_and_run_mapping_code(response, dataset="training", task_id="e8593010")

        assert "Please take your time to think about the problem and then" in return_value
