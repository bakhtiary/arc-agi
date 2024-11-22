# Run test with ```.venv/bin/python -m unittest state_machine_solver_utils_test.py -v```
    
from pathlib import Path
import unittest

from dataset import LocalDataset
from state_machine_solver_utils import extract_and_run_mapping_code

current_file_dir = Path(__file__).parent

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
        return_value = extract_and_run_mapping_code(response, task_id='e8593010', dataset=LocalDataset('training'))

        self.assertIn('Please take your time to think about the problem and then', return_value[-1]['text'])


    def test_tools_work(self):
        response = '''```
def solve(grid: list[list[int]]) -> list[list[int]]:
    # Extract objects from the grid
    objects = get_grid_objects_as_flat_list(grid, univalued=False, diagonal=False, with_bg=False, bg_color=BLACK)

    # Sort objects by their color order in the input grid
    objects.sort(key=lambda obj: min(idx[1] for idx, color in obj))
    ...
```
'''
        tools_codes = Path(current_file_dir / 'tools_src_mini.py').read_text()
        response2 = f'```\n{tools_codes}\n```\n\n' + response
        return_value = extract_and_run_mapping_code(response2, task_id='846bdb03', dataset=LocalDataset('training'))
        return_value_str = '\n'.join(msg['text'] for msg in return_value if 'text' in msg)
        self.assertIn("'get_grid_objects_as_flat_list' is not defined", return_value_str)
        
        return_value = extract_and_run_mapping_code(response, task_id='846bdb03',
            dataset=LocalDataset('training'), tool_codes=tools_codes)
        return_value_str = '\n'.join(msg['text'] for msg in return_value if 'text' in msg)
        self.assertNotIn("'get_grid_objects_as_flat_list' is not defined", return_value_str)

    def test_extra_code_block_error(self):
        response = '''
```python
def solve(grid: list[list[int]]) -> list[list[int]]:
    # Define the background color
    BLACK = 0

    # Extract unique non-background colors in row-major order
    unique_colors = []
    seen = set()
    for row in grid:
        for color in row:
            if color != BLACK and color not in seen:
                unique_colors.append(color)
                seen.add(color)

    # If no colors are present, return a grid filled with the background color
    if not unique_colors:
        return [[BLACK for _ in range(7)] for _ in range(7)]

    n_colors = len(unique_colors)
    output = [[BLACK for _ in range(7)] for _ in range(7)]

    # To match the expected output, we apply a shift of +1 in the color indexing
    shift = 1

    for i in range(7):
        for j in range(7):
            # Calculate the shifted index for cyclic color assignment
            color_index = (i + j + shift) % n_colors
            output[i][j] = unique_colors[color_index]

    return output
```

**Explanation of the Corrections:**

1. **Shift in Color Indexing**:
    - **Issue**: The initial implementation used `color_index = (i + j) % n_colors`, which started the color cycle with the first unique color. However, the expected output required starting the cycle with the second color in the `unique_colors` list.
    - **Solution**: Introduced a `shift` variable set to `1`. This shifts the color indexing by one position, ensuring that the cycle starts with the second color. The updated line is:
      ```python
      color_index = (i + j + shift) % n_colors
      ```

2. **Handling Background Colors**:
    - **Clarification**: Defined `BLACK = 0` to make the code more readable and to adhere to the provided constants. This ensures that background colors are correctly identified and handled.
# ...
Given the input grid:
```
[
 [0, 0, 0, 0, 0, 0, 0],
 # ...
]
```
'''
        return_value = extract_and_run_mapping_code(response, task_id='05269061', dataset=LocalDataset('training'))
        return_value_str = '\n'.join(msg['text'] for msg in return_value if 'text' in msg)
        self.assertNotIn("NameError: name 'i' is not defined", return_value_str)
