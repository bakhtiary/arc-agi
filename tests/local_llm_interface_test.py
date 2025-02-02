# import unittest

# import requests
# import io

# import json
# import numpy as np
# import pandas as pd
# from PIL import Image
# from pathlib import Path
# import matplotlib.pyplot as plt
# import torch
# from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

# from image_utils import pil_image_to_base64
# from local_llm_interface import QwenLocalLLMInterface
# from llm_utils import HistoryManager, chat_with_llm

# class TestQwenLocalLLMInterface(unittest.TestCase):
#     def __init__(self):
#         super().__init__()
#         url = 'https://storage.googleapis.com/kaggle-organizations/3733/thumbnail.png'
#         response = requests.get(url)
#         image = Image.open(io.BytesIO(response.content))        
#         self.history_manager = HistoryManager()

#         with self.history_manager.start_new_message('user', QwenLocalLLMInterface.TEXT_ADVANCED):
#             self.history_manager.add_text('Describe this image')            
#             self.history_manager.add_image(pil_image_to_base64(image))

#     def test_messages_to_local_llm_format(self):
#         self.local_llm_interface = QwenLocalLLMInterface()
#         results = self.local_llm_interface.messages_to_local_llm_format(self.history_manager.get_messages())
#         self.assertEqual(results,[
#             {
#                 'role': 'user',
#                 'content': [
#                     {'type': 'text', 'text': 'Describe this image'},
#                     {'type': 'image'},
#                 ],
#             },
#         ])

#     def test_chat_with_llm(self):
#         self.local_llm_interface = QwenLocalLLMInterface(timeout_seconds=1)

#         reply = chat_with_llm(self.local_llm_interface, self.history_manager, 'qwen')
#         print(f'reply: {reply}')
#         self.assertTrue(len(reply) > 2)



# # TestQwenLocalLLMInterface().test_messages_to_local_llm_format()
# TestQwenLocalLLMInterface().test_chat_with_llm()