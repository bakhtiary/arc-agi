import re
import subprocess


def extract_and_run_mapping_code(response, dataset: str, task_id: str):
    code = extract_code(response)
    print(code)
    print(code)
    return run_code_read_outputs_with_timeout(dataset, task_id, code.encode(), 10)

def extract_and_run_lens_code(response, task):
    pass

def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join(code_blocks)
        return code
    else:
        return None


def run_code_read_outputs_with_timeout(dataset, task_id, code, timeout_seconds: int):
    proc = subprocess.Popen(['python', 'state_machine_solver_code_runner.py', dataset, task_id], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    return outs.decode()
