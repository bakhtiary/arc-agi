import json
import subprocess

from dataset import Dataset


def run_any_code_read_outputs_with_timeout(args: list[str], code: bytes, timeout_seconds: int,
                                       python_file) -> list[dict]:
    proc = subprocess.Popen(['python', python_file] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # TODO: We could have also openned pipes streams in text mode by passing text=True and then code would be a str
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        return []
    
    jsonls = outs.decode()
    results = []
    
    for jsonl in jsonls.splitlines():
        if jsonl.strip() == '':
            continue
        try: # handle possible unstructured output from solve_fn 
            results.append(json.loads(jsonl.strip()))
        except json.JSONDecodeError as e:
            if not hasattr(e, 'ak_data'):
                e.ak_data = {}
            e.ak_data['state_machine_solver_utils'] = {
                'exception': e,
                'jsonls': jsonls
            }

    return results
