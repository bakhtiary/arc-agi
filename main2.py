# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

import base64
import io
import json
import os
import traceback
import re
from pathlib import Path
from datetime import datetime
from typing import Counter

import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import litellm
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

DATA_DIR = Path('data')
LOG_DIR = Path('log') / datetime.now().strftime('%Y%m%d-%H%M%S')

NUM_BEAMS=100
MAX_ATTEMPTS = 3
LLM_NUM_RETRIES = 2
#LLM_MODEL='gpt-3.5-turbo'
LLM_MODEL='gpt-4o'

ARC_COLORS = [
    '#000',
    '#0074D9',  # /* blue */
    '#FF4136',  # /* red */
    '#2ECC40',  # /* green */
    '#FFDC00',  # /* yellow */
    '#AAAAAA',  # /* grey */
    '#F012BE',  # /* fuschia */
    '#FF851B',  # /* orange */
    '#7FDBFF',  # /* teal */
    '#870C25',  # /* brown */
]
arc_cmap = ListedColormap(ARC_COLORS)

def beam_solve(task_id, dataset, num_beams):
    results = []
    print(f"Solving {task_id}")
    for attempt_i in range(num_beams):
        filename = LOG_DIR / task_id / (str(attempt_i)+".json")
        filename.parent.mkdir(parents=True, exist_ok=True)
        result = solve(task_id, dataset, filename)
        if result is not None:
            results.append(result)
    if results:
        print(f"we managed to solve {task_id}")
    else :
        print(f"we failed to solve {task_id}")
    tupled_results = list_to_tuple_rec(results)
    counts = Counter(tupled_results)
    return tuple_to_list_rec(counts.most_common())

def messages_to_md(messages):
    md = ''
    for message_i, message in enumerate(messages, 1):
        role, content = message['role'], message['content']
        md += f'# {message_i} - {role}\n'
        if isinstance(content, str):
            md += f'{content}\n'
        else:
            for ci, c in enumerate(content, 1):
                md += f'## {ci}\n' 
                if c['type'] == 'image_url':
                    md += f'[image]\n'
                elif c['type'] == 'text':
                    md += f'{c["text"]}\n'

        md += '\n'
    return md


def save_messages(messages, logfile):
    with open(logfile, "w") as fp:
        json.dump(messages, fp, indent=4)

    with open(str(logfile) + ".md", "w") as fp:
        fp.write(messages_to_md(messages))
            

def solve(task_id, dataset, logfile):
    task = read_task(task_id, dataset)

    messages = []
    add_content_to_messages(messages, 'system', 'You are an intelligent assistant and a Python expert.')
    setup_to_analyze_problem(messages, task)
    chat_with_llm(messages)
    setup_to_ask_for_first_solution(messages, task)

    for attempt_i in range(MAX_ATTEMPTS):
        chat_with_llm(messages)
        save_messages(messages, logfile)

        code = extract_code(messages[-1]['content'][0]['text'])
        if code is None:
            send_short_message(messages, 'Please provide the code enclosed in triple backticks.')
        else:
            err_content, result = verify_code(code, task)
            if err_content:
                add_content_to_messages(messages, 'user', err_content)
            else:
                return result


# Define the exceptions that should trigger a retry
retry_exceptions = (
    Exception,  # Replace with specific exceptions if litellm defines any
)
def add_content_to_messages(messages, role, content):
    assert isinstance(content, list) or isinstance(content, str)
    if isinstance(content, str):
        content_str = content
        content = []
        add_text_to_content(content, content_str)

    messages.append({
        'role': role,
        'content': content    
    })
    
def make_image_base64(input_grid):

    plt.imshow(input_grid, cmap=arc_cmap, vmin=0, vmax=10)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData

def add_image_to_content(content, grid):
    base64_img = make_image_base64(grid)
    content.append({
        'type': 'image_url',
        'image_url': {
            'url': f'data:image/jpeg;base64,{base64_img}'
        }
    })

def add_text_to_content(content, text):
    content.append({
        'type': 'text',
        'text': text
    })


@retry(
    retry=retry_if_exception_type(retry_exceptions),
    stop=stop_after_attempt(LLM_NUM_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def chat_with_llm(messages):
    response = litellm.completion(
        messages=messages,
        stream=False,
        model=LLM_MODEL,
        max_tokens=4096,
        temperature=0,
    )
    assistant_reply = response.choices[0]['message']['content'].strip()
    add_content_to_messages(messages, 'assistant', assistant_reply)
    return assistant_reply

def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join(code_blocks)
        return code
    else:
        return None


def setup_to_analyze_problem(messages, task):
    content = []
    add_text_to_content(content, ('Can you analyze the following pair of images and find the '
        'input/output relationship between them? (the first is the input and the second is the output)'))
    add_image_to_content(content, task['train'][0]['input'])
    add_image_to_content(content, task['train'][0]['output'])
    add_content_to_messages(messages, 'user', content)

def setup_to_ask_for_first_solution(messages, task):
    content = []
    add_text_to_content(content, ('Good. Now write a Python function named `solve` that trasnfers the input as a grid to the output as a grid.'
            f'\nGrids are represented as Python list of lists. For instance, the input and ouput grids for the first pair of images are: '
            f'\n\nInput: ' + str(task['train'][0]['input']) +
            f'\n\nOutput: ' + str(task['train'][0]['output']) +
            f'\n\nPlease enclose code in triple backticks as usual.'
            # TODO: One shot example
    ))
    add_content_to_messages(messages, 'user', content)

def send_short_message(messages, text):
    add_content_to_messages(messages, 'user', text)
    assistant_reply = chat_with_llm(messages)
    return assistant_reply


def grid_is_correct(pred_grid):
    try:
        t = np.array(pred_grid)
        return len(t.shape) == 2
    except:
        return False



def verify_code(code: str, task: dict): # TODO run task in another thread or process for a limited amount of time
    err_content = []
    try:
        local_namespace = {}
        exec(code, {}, local_namespace)
    except Exception:
        error_msg = traceback.format_exc()
        add_text_to_content(err_content, (f'The following error happened when evaluating your function `solve`:'
            f'\n{error_msg}\n'
            'Please write a corrected code enclosed in triple backticks.')                                 
        )
        return err_content, None
    
    if 'solve' not in local_namespace:
        add_text_to_content(err_content, ('Function `solve` is not defined.'
            'Please try again and make sure the code is enclosed in triple backticks.'))
        return err_content, None
    else:
        solve_fp = local_namespace['solve']
        for pair in task['train']:
            input_grid, output_grid = pair['input'], pair['output']
            try:
                pred_grid = solve_fp(input_grid)
            except Exception:
                error_msg = traceback.format_exc()
                add_text_to_content(err_content, (f'The following error happened when calling your function `solve`:'
                    f'\n{error_msg}\n'
                    f'The input was: {str(input_grid)}'
                    'Please write a corrected code enclosed in triple backticks.')                                 
                )
                return err_content, None
            
            if output_grid != pred_grid:
                add_text_to_content(err_content, f'Wrong output for input: `{str(input_grid)}`')
                add_image_to_content(err_content, input_grid)
                add_text_to_content(err_content, f'Expected output: `{str(output_grid)}`')
                add_image_to_content(err_content, output_grid)
                if grid_is_correct(pred_grid):
                    add_text_to_content(err_content, f'Output generated by your code: `{str(pred_grid)}`')
                    add_image_to_content(err_content, pred_grid)
                else:
                    add_text_to_content(err_content, f'The output generated by your code was not a 2d grid. it was: `{str(pred_grid)}`')
                add_text_to_content(err_content, 'Please take your time to think about the problem and then write a corrected code enclosed in triple backticks.')
                return err_content, None
        
        pred_grid_for_test = local_namespace['solve'](task['test'][0]['input'])
        return None, pred_grid_for_test
    

def read_task(task_id, dataset):
    json_text = (DATA_DIR / dataset / f'{task_id}.json').read_text()
    return json.loads(json_text)


def list_to_tuple_rec(obj):
    if not isinstance(obj, list):
        return obj
    else:
        return tuple([list_to_tuple_rec(e) for e in obj])


def tuple_to_list_rec(obj):
    if not isinstance(obj, tuple):
        return obj
    else:
        return [tuple_to_list_rec(e) for e in obj]



if __name__ == "__main__":
    training_dir = "data/training"
    task_ids = [f.split(".")[0] for f in os.listdir(training_dir)] [6:]
    for task_id in task_ids:
        beam_solve(task_id, 'training', num_beams=1)
