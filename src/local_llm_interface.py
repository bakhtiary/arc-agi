import os
import signal
import sys
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

from image_utils import base64_to_pil_image
from llm_utils import LLMInterface

# check_point = '/kaggle/input/qwen2-vl/transformers/qwen2-vl-7b-instruct/1/'
check_point = 'Qwen/Qwen2-VL-7B-Instruct'
model = Qwen2VLForConditionalGeneration.from_pretrained(check_point, torch_dtype=torch.bfloat16, device_map="auto")
processor = AutoProcessor.from_pretrained(check_point)

class TimeoutException(Exception):
    pass

def handler(signum, frame):
    os.kill(os.getpid(), signal.SIGINT)
    raise TimeoutException("The model.generate() call timed out.")

class QwenLocalLLMInterface(LLMInterface):
    def __init__(self, timeout_seconds: int=None):
        super().__init__()
        self.timeout_seconds = timeout_seconds


    def messages_to_local_llm_format(self, messages):
        results = []

        for msg in messages:
            role, content = msg['role'], msg['content']
            if isinstance(content, str):
                results.append({'role': role, content: [{'type': 'text', 'text': content}]})
                continue

            new_content = []
            for item in content:
                if item['type'] == 'text':
                    new_content.append(item)
                elif item['type'] == 'image_url':
                    new_content.append({'type': 'image'})
                else:
                    raise ValueError(f'unsupported type `{item["type"]}` in content.')
            
            results.append({'role': role, 'content': new_content})

        return results
    
    def get_messages_images_as_pil_images(self, messages):
        results = []

        for msg in messages:
            role, content = msg['role'], msg['content']
            if not isinstance(content, list):
                continue

            for item in content:
               if item['type'] == 'image_url':
                    results.append(base64_to_pil_image(item['image_url']['url'].removeprefix('data:image/jpeg;base64,')))
        
        return results

    def chat_with_llm(self, messages, llm, resp_format=None):
        if resp_format is not None:
            raise NotImplementedError('resp_format not supported for local llms')
        
        return self.chat_with_llm_simple(messages, llm)


    def chat_with_llm_simple(self, messages, llm):
        if self.timeout_seconds is not None:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(self.timeout_seconds)

        try:
            new_messages = self.messages_to_local_llm_format(messages)
            text = processor.apply_chat_template(new_messages, tokenize=False, add_generation_prompt=True)
            images = self.get_messages_images_as_pil_images(messages)
            inputs = processor(text=[text], images=images, return_tensors="pt")
            inputs = inputs.to(model.device)
            generated_ids = model.generate(**inputs, max_new_tokens=128, max_time=self.timeout_seconds)
            generated_ids = generated_ids[0, inputs.input_ids.shape[1]:]
            assistant_reply = processor.decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            return assistant_reply
        except TimeoutException:
            return ''
        except KeyboardInterrupt:
            return ''
        finally:
            if self.timeout_seconds is not None:
                signal.alarm(0)

        