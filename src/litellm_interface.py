import litellm
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

    def chat_with_llm_simple_(self, messages, llm: str):
        if 'o1' in llm:
            response = litellm.completion(
                messages=messages,
                stream=False,
                model=llm,
                max_completion_tokens=25000,                
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
