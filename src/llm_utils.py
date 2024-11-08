import json
import re
import threading

from pydantic import BaseModel

import litellm
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from log_utils import add_string_to_log, message_to_md


# def add_content_to_messages_and_log(messages, role, content, log_file, llm=None):
#     assert isinstance(content, list) or isinstance(content, str)
#     if isinstance(content, str):
#         content_str = content
#         content = []
#         add_text_to_content(content, content_str)

#     message = {
#         'role': role,
#         'content': content
#     }
#     messages.append(message)
#     add_string_to_log(message_to_md(message, False, llm), log_file)


# def add_image_to_content(content, grid):
#     if isinstance(grid, list):
#         base64_img = single_grid_to_base64(grid)
#     elif isinstance(grid, str): # already base64 ecnoded
#          base64_img = grid
#     else:
#         raise Exception(f'grid of type {type(grid)} not supported.')
#     content.append({
#         'type': 'image_url',
#         'image_url': {
#             'url': f'data:image/jpeg;base64,{base64_img}'
#         }
#     })


# def add_text_to_content(content, text):
#     content.append({
#         'type': 'text',
#         'text': text
#     })


def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join(code_blocks)
        return code
    else:
        return None
    

class HistoryManager:
    def __init__(self, log_file=None):
        self.messages = []
        self._thread_local = threading.local()  # Thread-local storage
        self.log_file = log_file

    def start_new_message(self, role, llm, log_at_end=True):
        self._thread_local.temp_role = role
        self._thread_local.temp_llm = llm
        self._thread_local.temp_log_at_end = log_at_end
        return self

    def __enter__(self):
        self._thread_local.temp_content = []
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self._thread_local, 'temp_content') and self._thread_local.temp_content:
            message = {
                'role': self._thread_local.temp_role,
                'content': self._thread_local.temp_content
            }
            self.messages.append(message)
            if self._thread_local.temp_log_at_end and self.log_file is not None:
                add_string_to_log(message_to_md(message, False, self._thread_local.temp_llm),
                    self.log_file)


    def add_singletone_text_message(self, role, text, llm):
        with self.start_new_message(role, llm):
            self.add_text(text)
        
    def add_image(self, grid):
        if isinstance(grid, list):
            base64_img = single_grid_to_base64(grid)
        elif isinstance(grid, str): # already base64 ecnoded
            base64_img = grid
        else:
            raise Exception(f'grid of type {type(grid)} not supported.')
        self._thread_local.temp_content.append({
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{base64_img}'
            }
        })
            
    def add_text(self, text):
        self._thread_local.temp_content.append({
            'type': 'text',
            'text': text
        })

    def get_messages(self):
        return self.messages
    
    def chat_with_llm(self, llm, resp_format=None):
        return chat_with_llm(self.get_messages(), llm, resp_format)
        

def chat_with_llm(messages, llm, resp_format=None):
    if resp_format is None:
        return chat_with_llm_simple(messages, llm)
    else:
        return chat_with_llm_with_format(messages, llm, resp_format)

def chat_with_llm_simple(messages, llm):
    if 'o1' in llm:
        response = litellm.completion(
            messages=messages,
            stream=False,
            model=llm,
            max_completion_tokens=25000,
            temperature=0.1,
        )
    else:
        response = litellm.completion(
            messages=messages,
            stream=False,
            model=llm,
            max_tokens=4096,
            temperature=0.1,
        )
    assistant_reply = response['choices'][0]['message']['content'].strip()
    return assistant_reply

def chat_with_llm_with_format(messages, llm, resp_format: type[BaseModel]):
    if 'o1' in llm:
        response = litellm.completion(
            messages=messages,
            stream=False,
            model=llm,
            max_completion_tokens=25000,
            temperature=0.2,
            response_format=resp_format
        )
    else:
        response = litellm.completion(
            messages=messages,
            stream=False,
            model=llm,
            max_tokens=4096,
            temperature=0.2,
            response_format=resp_format
        )
    assistant_reply = response['choices'][0]['message']['content'].strip()
    if isinstance(assistant_reply, str):
        return resp_format.model_validate_json(assistant_reply)
    elif isinstance(assistant_reply, dict):
        return resp_format.model_validate_strings(assistant_reply)
    
    return assistant_reply


    