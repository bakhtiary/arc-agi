import base64
import json
from pathlib import Path
import io

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from openai import OpenAI

NUM_BEAMS = 3
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


def solve_one(task_number, interactive=True):
    task = read_task(task_number)
    conversation = [{'role': 'user', 'content': [{
        'type': 'text',
        'text': 'The first image is the input and the second image is the output. what is the relation ship between these two images'
    }]}]

    last_image_index = 0
    while True:
        if interactive:
            next_instruction = input('What should I do next? (1 <text> (send free text), 2 (sends next image), 3 (quit)) ')
        else:
            # if last_image_index < len(task['train']):
            if last_image_index == 0:
                next_instruction = '2'
            else:
                next_instruction = '3'

        if next_instruction[0] == '3':
            break

        if next_instruction[0] == '1':
            conversation.append(
                {'role': 'user', 'content': [{
                    'type': 'text',
                    'text': next_instruction[1:].strip()
                }]}
                )
        elif next_instruction[0] == '2':
            if last_image_index == len(task['train']):
                print('No more image to send')
                continue
            conversation = add_images_to_conversation(conversation,
                task['train'][last_image_index]['input'],
                task['train'][last_image_index]['output'])
            last_image_index += 1
        
        conversation = make_chatgpt_query(conversation)
        print(f"{conversation[-1]['content'][0]['text']}")


client = OpenAI()

def add_images_to_conversation(conversation, input_grid, output_grid):
    input_img = make_image_base64(input_grid)
    plt.savefig('im1.jpg', format='jpg')
    output_image = make_image_base64(output_grid)
    plt.savefig('im2.jpg', format='jpg')
    conversation.append(
        {'role': 'user', 'content':[{
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{input_img}'
            }
        },
        {
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{output_image}'
            }
        }]}
    )
    return conversation

def make_chatgpt_query(conversation):
    completion = client.chat.completions.create(
        model='gpt-4o',
        messages=conversation
    )
    conversation.append( {'role': 'assistant', 'content': [{
                    'type': 'text',
                    'text': completion.choices[0].message.content
                }]})
    return conversation


def make_image_base64(input_grid):
    plt.imshow(input_grid, cmap=arc_cmap, vmin=0, vmax=10)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData


def read_task(task_number):
    with open(f'data/training/{task_number}') as f:
        return json.load(f)


def solve_all(task_number, interactive=True):
    for i in range(NUM_BEAMS):
        solve_one(task_number, interactive=interactive)


def main(interactive):
    for task_number in Path('test').iterdir():
        solve_all(task_number, interactive=interactive)

if __name__ == '__main__':
    solve_one('f8b3ba0a.json', interactive=False)
    # main()
