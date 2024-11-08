import json
from pathlib import Path

def read_jsonl(file_path):
    objs = []
    with open(file_path, 'r') as file:
        for line in file:
            objs.append(json.loads(line.strip()))
    return objs

def write_jsonl(objs: list, file_path):
    with open(file_path, 'w') as file:
        for entry in objs:
            file.write(json.dumps(entry) + '\n')

def append_jsonl(obj, file_path):
    with open(file_path, 'a+') as file:
        file.write(json.dumps(obj) + '\n')


def create_empty_log(log_file):
    Path(log_file).touch()

def add_string_to_log(log_portion: str, log_file):
    if isinstance(log_file, Path | str): 
        with open(log_file, 'a+') as fp:
            fp.write(log_portion)
    elif hasattr(log_file, 'write'):
        log_file.write(log_portion)
    else:
        raise Exception(f'Cannot log into {log_file}') 

def message_to_md(message, prune_images, llm=None):
    md = ''
    role, content = message['role'], message['content']
    md += f'----\n\n'
    md += f'# {role} ({llm}):\n\n'
    if isinstance(content, str):
        md += f'{content}\n'
    else:
        for ci, c in enumerate(content, 1):
            if c['type'] == 'image_url':
                if prune_images:
                    md += f'[image]\n'
                else:
                    md += f'<img src="{c["image_url"]["url"]}" />\n'
            elif c['type'] == 'text':
                md += f'{c["text"]}\n'

    md += '\n'
    return md


def add_item_to_big_log(task_id, dataset, termination_reason, score, results_json_file, error_data=None, error_ak_data=None):
    assert termination_reason in ['success', 'error', 'timeout', 'n/a']
    log_obj = {
        'task_id': task_id,
        'dataset': dataset.dataset_location,
        'termination_reason': termination_reason,
        'score': score
    }

    if error_data is not None:
        log_obj['error_data'] = repr(error_data)
        assert error_ak_data is not None
        log_obj['error_ak_data'] = repr(error_ak_data)

    append_jsonl(log_obj, results_json_file)
    
    