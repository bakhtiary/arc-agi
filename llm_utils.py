import json
import re
from image_utils import make_all_in_one_images_base64, make_image_base64


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

def save_messages(messages, log_file):
    with open(log_file, 'w') as fp:
        json.dump(messages, fp, indent=4)

    with open(str(log_file).removesuffix('.json') + '.md', 'w') as fp:
        fp.write(messages_to_md(messages, prune_images=True))

    with open(str(log_file).removesuffix('.json') + '.full.md', 'w') as fp:
        fp.write(messages_to_md(messages, prune_images=False))


def messages_to_md(messages, prune_images):
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
                    if prune_images:
                        md += f'[image]\n'
                    else:
                        md += f'<img src="{c["image_url"]["url"]}" />\n'
                elif c['type'] == 'text':
                    md += f'{c["text"]}\n'

        md += '\n'
    return md


def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join(code_blocks)
        return code
    else:
        return None