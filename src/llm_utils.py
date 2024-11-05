import json
import re
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from log_utils import add_string_to_log, message_to_md


def add_content_to_messages_and_log(messages, role, content, log_file, llm=None):
    assert isinstance(content, list) or isinstance(content, str)
    if isinstance(content, str):
        content_str = content
        content = []
        add_text_to_content(content, content_str)

    message = {
        'role': role,
        'content': content
    }
    messages.append(message)
    add_string_to_log(message_to_md(message, False, llm), log_file)


def add_image_to_content(content, grid):
    if isinstance(grid, list):
        base64_img = single_grid_to_base64(grid)
    elif isinstance(grid, str): # already base64 ecnoded
         base64_img = grid
    else:
        raise Exception(f'grid of type {type(grid)} not supported.')
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


def add_all_in_one_images_to_content(content: list, all_pairs: list[tuple]):
    raise DeprecationWarning()
    base64_img = grids_all_in_one_to_base64(all_inputs)
    content.append({
        'type': 'image_url',
        'image_url': {
            'url': f'data:image/jpeg;base64,{base64_img}'
        }
    })

def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join(code_blocks)
        return code
    else:
        return None