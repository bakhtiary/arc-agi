from abc import abstractmethod
import copy
from io import IOBase
import json
from pathlib import Path
import re
import threading
import warnings

from image_utils import single_grid_to_base64
from log_utils import add_string_to_log, message_to_md


def extract_code(assistant_reply):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', assistant_reply, re.DOTALL)
    if code_blocks:
        code = '\n'.join([code_block.strip() for code_block in code_blocks])
        return code
    else:
        return None

class LLMInterface:
    TEXT_ADVANCED = 'text-advanced'
    TEXT = 'text'
    VISION = 'vision'

    vision_model_name: str
    text_model_name: str

    @abstractmethod
    def chat_with_llm(self, messages, llm: str, resp_format=None):
        return
    
    @abstractmethod
    def llm_name_translate(self, generic_name):
        return
    
    def get_llms_mapping(self):
        result = {}
        generic_names = [LLMInterface.TEXT_ADVANCED, LLMInterface.TEXT, LLMInterface.VISION]
        for generic_name in generic_names:
            result[generic_name] = self.llm_name_translate(generic_name)
        return result

        
class HistoryManager:
    def __init__(self, log_file:Path|IOBase=None):
        self.messages, self.ttls, self.tsts = [], [], []
        self._thread_local = threading.local()  # Thread-local storage
        self.log_file = log_file

    def start_new_message(self, role, llm, log_at_end=True, ttl=None, tst=None):
        self._thread_local.temp_role = role
        self._thread_local.temp_llm = llm
        self._thread_local.temp_log_at_end = log_at_end
        self._thread_local.temp_ttl = ttl
        self._thread_local.temp_tst = tst
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
            self.ttls.append(self._thread_local.temp_ttl)
            self.tsts.append(self._thread_local.temp_tst)        
            if self._thread_local.temp_log_at_end and self.log_file is not None:
                add_string_to_log(message_to_md(message, False, self._thread_local.temp_llm),
                    self.log_file)


    def add_singletone_text_message(self, role, text, llm, log_at_end=True, ttl=None, tst=None):
        with self.start_new_message(role, llm, log_at_end, ttl, tst):
            self.add_text(text)
        
    def add_image(self, grid):
        if isinstance(grid, list):
            base64_img = single_grid_to_base64(grid)
        elif isinstance(grid, str): # already base64 ecnoded
            base64_img = grid
        else:
            warnings.warn(f'grid of type {type(grid)} not supported. Please pass a grid or a base64 image.')
            
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

    def get_messages(self, cur_tst=None):
        if cur_tst is None:
            return self.messages
        assert len(self.messages) == len(self.ttls) == len(self.tsts)
        return [msg for msg, ttl, tst in zip(self.messages, self.ttls, self.tsts)
            if ttl == None or tst == None or ttl >= cur_tst - tst]
        
    def pop_messages(self, num_to_pop):
        del self.messages[-num_to_pop:]
        del self.ttls[-num_to_pop:]
        del self.tsts[-num_to_pop:]
   
    def set_ttl_last_pair(self, one_before_last_ttl, last_ttl):
        self.ttls[-2], self.ttls[-1] = one_before_last_ttl, last_ttl

    def set_ttl_last_elem(self, last_ttl):
        self.ttls[-1] = last_ttl

def chat_with_llm(llm_intreface: LLMInterface, histoy_manager: HistoryManager,
    llm: str, resp_format=None, cur_tst=None):
        return llm_intreface.chat_with_llm(
            histoy_manager.get_messages(cur_tst=cur_tst), llm, resp_format)
