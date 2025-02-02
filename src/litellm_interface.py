import json
import os
import litellm
import requests
from llm_utils import LLMInterface
from pydantic import BaseModel


class LiteLLMInterface(LLMInterface):
    def __init__(self, vision_model, text_model):
        self.vision_model = vision_model
        self.text_model = text_model

    def llm_name_translate(self, llm_tag):
        if 'text' in llm_tag:
            return self.text_model
        else:
            return self.vision_model

        
    def chat_with_llm(self, messages, llm_tag: str, resp_format=None):
        if llm_tag in [LLMInterface.TEXT, LLMInterface.TEXT_ADVANCED]:
            messages = self.prune_images(messages)
        llm = self.llm_name_translate(llm_tag)
        if resp_format is None:
            return self.chat_with_llm_simple_(messages, llm)
        else:
            return self.chat_with_llm_with_format_(messages, llm, resp_format)

    def chat_via_fireworks(self, messages, llm: str):
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        payload = {
            "model": llm.removeprefix('fireworks/'),
            "max_tokens": 20480,
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": messages
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['FIREWORKS_API_KEY']}"
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        return response.json()
    
    def chat_via_llama_cpp(self, messages, llm: str):
        url = "http://localhost:8080/v1/chat/completions"
        payload = {
            # "model": llm.removeprefix('fireworks/'),
            "max_tokens": 20480,
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": messages
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {os.environ['FIREWORKS_API_KEY']}"
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        return response.json()

    def chat_with_llm_simple_(self, messages, llm: str):
        if llm.startswith('fireworks/'):
            response = self.chat_via_fireworks(messages, llm)
        elif llm.startswith('llama.cpp/'):
            response = self.chat_via_llama_cpp(messages, llm)
        elif 'o1' in llm:
            response = litellm.completion(
                messages=messages,
                stream=False,
                model=llm,
                max_completion_tokens=25000,                
            )
            cost = litellm.completion_cost(response)
            print(f'$$$$$$$$$$$ ===> ${cost}')
        else:
            response = litellm.completion(
                messages=messages,
                stream=False,
                model=llm,
                max_tokens=4096,
                temperature=0.1,
            )
            cost = litellm.completion_cost(response)
            print(f'$$$$$$$$$$$ ===> ${cost}')
        assistant_reply = response['choices'][0]['message']['content'].strip()
        if '</think>' in assistant_reply:
            assistant_reply = assistant_reply.split('</think>')[1].strip()
            assert '</think>' not in assistant_reply
        return assistant_reply

    def chat_with_llm_with_format_(self, messages, llm: str, resp_format: type[BaseModel]):
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
