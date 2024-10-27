import re
import subprocess

from llm_utils import extract_code


def extract_and_run_mapping_code(response, task_id: str, dataset: str):
    code = extract_code(response)
    # Todo what if code is "none"
    return run_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 10, 'state_machine_solver_code_runner.py')

def extract_and_run_lens_code(response, task_id: str, dataset: str):
    code = extract_code(response)
    return run_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 10, 'state_machine_solver_lens_runner.py')

def run_code_read_outputs_with_timeout(task_id, dataset, code, timeout_seconds: int,
                                       python_file):
    proc = subprocess.Popen(['python', python_file, task_id, dataset], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    return outs.decode()
