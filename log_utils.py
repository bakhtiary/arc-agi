import json

def create_empty_log(log_file):
    save_log({}, log_file)

def save_log(messages, log_file):
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


def add_termination_to_log(log_file, score):
    ...