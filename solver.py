import json
import re
import traceback
from pathlib import Path
from collections import Counter

import litellm
import numpy as np
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from image_utils import make_image_base64, make_all_images_base64
from task_utils import read_task

# litellm.set_verbose = True

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

NUM_BEAMS=100
MAX_ATTEMPTS = 3
LLM_NUM_RETRIES = 2
LLM_MODEL='gpt-4o'


def beam_solve(task_id, dataset, num_beams, log_dir, msg):
    try:
        return do_beam_solve(task_id, dataset, num_beams, log_dir, msg)
    except Exception as e:
        error_msg = traceback.format_exc()
        e = Exception(error_msg)
        e.ak_data = {'task_id': task_id, 'dataset': dataset}
        raise e


def do_beam_solve(task_id, dataset, num_beams, log_dir, msg):
    (log_dir / task_id).mkdir(parents=True, exist_ok=True)
    results: list[list[AKGrid]] = []
    print(f'Solving {task_id} [{msg}]')
    for beam_i in range(num_beams):
        log_file = log_dir / task_id / f'{beam_i+1}.json'
        result = solve(task_id, dataset, log_file)
        if result is not None:
            results.append(result)
    if results:
        final_results_all: list[list[AKGrid]] = [] # for each test case, two solutions
        for test_i in range(len(results[0])):
            tupled_results = [grid_list2tuple(result[test_i]) for result in results]
            counts = Counter(tupled_results)
            # return log_dir, dataset, task_id, results[0]
            final_results: list[tuple[AKGridTuple, int]] = counts.most_common(2)
            if len(final_results) == 1:
                final_results = final_results * 2
            final_results: list[AKGrid] = [grid_tuple2list(e[0]) for e in final_results]
            final_results_all.append(final_results)
        return log_dir, dataset, task_id, final_results
    else:
        fake_final_results = [[[1]],[[1]]]
        return log_dir, dataset, task_id, fake_final_results

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


def solve(task_id, dataset, log_file: Path, max_attempts=MAX_ATTEMPTS) -> list[AKGrid]:
    task = read_task(task_id, dataset)

    messages = []
    add_content_to_messages(messages, 'system', 'You are an intelligent assistant and a Python expert.')
    setup_to_analyze_problem(messages, task)
    chat_with_llm(messages)
    setup_to_ask_for_first_solution(messages, task)

    for attempt_i in range(max_attempts):
        chat_with_llm(messages)
        save_messages(messages, log_file)

        code = extract_code(messages[-1]['content'][0]['text'])
        if code is None:
            send_short_message(messages, 'Please provide the code enclosed in triple backticks.')
        else:
            err_content, result = verify_code(code, task)
            if err_content:
                add_content_to_messages(messages, 'user', err_content)
            else:
                return result


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


def add_all_images_to_content(content, all_inputs):
    base64_img = make_all_images_base64(all_inputs)
    content.append({
        'type': 'image_url',
        'image_url': {
            'url': f'data:image/jpeg;base64,{base64_img}'
        }
    })


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
        'input/output relationship between them? In each row, the first is the input and the second is the output:'))
    # add_image_to_content(content, task['train'][0]['input'])
    # add_image_to_content(content, task['train'][0]['output'])
    add_all_images_to_content(content, task['train'])
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
            test_input_grid, output_grid = pair['input'], pair['output']
            try:
                pred_grid = solve_fp(test_input_grid)
            except Exception:
                error_msg = traceback.format_exc()
                add_text_to_content(err_content, (f'The following error happened when calling your function `solve`:'
                                                  f'\n{error_msg}\n'
                                                  f'The input was: {str(test_input_grid)}'
                                                  'Please write a corrected code enclosed in triple backticks.')
                                    )
                return err_content, None

            if output_grid != pred_grid:
                add_text_to_content(err_content, f'Wrong output for input: `{str(test_input_grid)}`')
                add_image_to_content(err_content, test_input_grid)
                add_text_to_content(err_content, f'Expected output: `{str(output_grid)}`')
                add_image_to_content(err_content, output_grid)
                if grid_is_correct(pred_grid):
                    add_text_to_content(err_content, f'Output generated by your code: `{str(pred_grid)}`')
                    add_image_to_content(err_content, pred_grid)
                else:
                    add_text_to_content(err_content, f'The output generated by your code was not a 2d grid. it was: `{str(pred_grid)}`')
                add_text_to_content(err_content, 'Please take your time to think about the problem and then write a corrected code enclosed in triple backticks.')
                return err_content, None
        
        pred_grid_for_tests = []
        test_input_grids = task['test']
        if isinstance(test_input_grids, dict) and 'input' in test_input_grids:
            test_input_grids = [test_input_grids]
        
        test_input_grids = [e['input'] for e in test_input_grids]
        for test_input_grid in test_input_grids:
            try:
                pred_grid_for_test = solve_fp(test_input_grid)
                pred_grid_for_tests.append(pred_grid_for_test)
            except Exception:
                error_msg = traceback.format_exc()
                add_text_to_content(err_content, (f'The following error happened when running the algorithm on the test input:'
                                                f'\n{error_msg}\n'
                                                f'The input was: {test_input_grid}'
                                                'Please write a corrected code enclosed in triple backticks.')
                                    )
                return err_content, pred_grid_for_tests

        return None, pred_grid_for_tests


def grid_list2tuple(grid: AKGrid) -> AKGridTuple:
    return tuple(tuple(row) for row in grid)


def grid_tuple2list(grid: AKGridTuple) -> AKGrid:
    return list(list(row) for row in grid)

