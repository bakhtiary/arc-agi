import re
import subprocess

from llm_utils import extract_code


def extract_and_run_mapping_code(response, task_id: str, dataset: str):
    code = extract_code(response)
    print(code)
    print(code)
    return run_code_read_outputs_with_timeout(task_id, dataset, code.encode(), 10)

def extract_and_run_lens_code(response, task):
    pass

def run_code_read_outputs_with_timeout(task_id, dataset, code, timeout_seconds: int):
    proc = subprocess.Popen(['python', 'state_machine_solver_code_runner.py', task_id, dataset], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    return outs.decode()
