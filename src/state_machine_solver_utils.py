from pathlib import Path
import re

from code_utils import run_any_code_read_outputs_with_timeout
from dataset import Dataset
from llm_utils import extract_code

current_file_directory = Path(__file__).parent


def extract_solve_fn(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    for code_block in code_blocks:
        if 'def solve' in code_block:
            return code_block
    return None

def extract_and_run_mapping_code(response, task_id: str, dataset: Dataset, tool_codes=None):
    # code = extract_solve_fn(response)
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your function `solve` in triple backticks.'''
    if tool_codes != None:
        code = tool_codes + '\n' + code
    return run_task_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 20, current_file_directory/'state_machine_solver_code_runner.py')

def extract_and_run_lens_code(response, task_id: str, dataset: Dataset):
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your functions in triple backticks.'''
    return run_task_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 20, current_file_directory/'state_machine_solver_lens_runner.py')

def run_task_code_read_outputs_with_timeout(task_id, dataset: Dataset, code: bytes, timeout_seconds: int,
                                       python_file):
    return run_any_code_read_outputs_with_timeout([task_id, dataset.string_encode()], code, timeout_seconds, python_file)

