import json
import re
from image_utils import make_all_in_one_images_base64, make_image_base64
from log_utils import save_log, message_to_md


def add_content_to_messages(messages, role, content, log_file):
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
    save_log(message_to_md(message, False), log_file)


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


def add_all_in_one_images_to_content(content: list, all_inputs: list[tuple]):
    base64_img = make_all_in_one_images_base64(all_inputs)
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