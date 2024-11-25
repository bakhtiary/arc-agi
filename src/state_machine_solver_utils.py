from pathlib import Path
import re

from code_utils import run_any_code_read_outputs_with_timeout
from dataset import Dataset
from llm_utils import extract_code, extract_code_keep_only_defs_and_imports

current_file_directory = Path(__file__).parent


def extract_solve_fn(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    for code_block in code_blocks:
        if 'def solve' in code_block:
            return code_block.strip()
    return None

def extract_and_run_mapping_code(response, task_id: str, dataset: Dataset, tools_code=None):
    code = extract_solve_fn(response)
    # code = extract_code(response), # Commented, as there might be code blocks in the explanation, such as this:
    #  ...
    #  - **Solution**: Introduced a `shift` variable set to `1`. This shifts the color indexing by one position, ensuring that the cycle starts with the second color. The updated line is:
    #   ```python
    #   color_index = (i + j + shift) % n_colors
    #   ```
    # ...
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your function `solve` in triple backticks.'''
    if tools_code is not None:
        code = tools_code + '\n' + code
    return run_task_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 20, current_file_directory/'state_machine_solver_code_runner.py')

def extract_and_run_mapping_code_with_lens(response, task_id: str, dataset: Dataset, tools_code=None, just_functions=True):
    code = extract_code_keep_only_defs_and_imports(response)
    # code = extract_code(response), # Commented, as there might be code blocks in the explanation, such as this:
    #  ...
    #  - **Solution**: Introduced a `shift` variable set to `1`. This shifts the color indexing by one position, ensuring that the cycle starts with the second color. The updated line is:
    #   ```python
    #   color_index = (i + j + shift) % n_colors
    #   ```
    # ...
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your functions `solve` and/or `lens_main` in triple backticks.'''
    if tools_code is not None:
        code = tools_code + '\n' + code
    return run_task_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 20, current_file_directory/'state_machine_solver_joint_code_runner.py')

def extract_and_run_lens_code(response, task_id: str, dataset: Dataset):
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your functions in triple backticks.'''
    return run_task_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 20, current_file_directory/'state_machine_solver_lens_runner.py')

def run_task_code_read_outputs_with_timeout(task_id, dataset: Dataset, code: bytes, timeout_seconds: int,
                                       python_file):
    return run_any_code_read_outputs_with_timeout([task_id, dataset.string_encode()], code, timeout_seconds, python_file)

