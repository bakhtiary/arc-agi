import json
import re
import subprocess
from pathlib import Path

from llm_utils import extract_code
from dataset import Dataset

current_file_directory = Path(__file__).parent

def extract_and_run_mapping_code(response, task_id: str, dataset: str):
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your function `solve` in triple backticks.'''
    return run_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 10, current_file_directory/'state_machine_solver_code_runner.py')

def extract_and_run_lens_code(response, task_id: str, dataset: str):
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your functions in triple backticks.'''
    return run_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 10, current_file_directory/'state_machine_solver_lens_runner.py')

def run_code_read_outputs_with_timeout(task_id, dataset: Dataset, code: bytes, timeout_seconds: int,
                                       python_file):
    proc = subprocess.Popen(['python', python_file, task_id, dataset.string_encode()], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # TODO: We could have also openned pipes streams in text mode by passing text=True and then code would be a str
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    jsonls = outs.decode()
    results = []
    for jsonl in jsonls.splitlines():
        if jsonl.strip() != '':
            results.append(json.loads(jsonl.strip()))
    return results
