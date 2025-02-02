from pathlib import Path
import tempfile
from unittest import TestCase

from dotenv import load_dotenv
import litellm

from litellm_interface import LiteLLMInterface
from llm_utils import HistoryManager, LLMInterface, extract_code


class TestExtractCode(TestCase):
    def TestExtractCode(self):
        text = "To address the issue, it seems the task is to replace the number `7` with `5`. Here's the corrected code:\n\n```python\ndef solve(input_grid):\n    # Transform the grid by replacing 7 with 5\n    output_grid = [\n        [5 if num == 7 else num for num in row]\n        for row in input_grid\n    ]\n    \n    return output_grid\n\n# Example input grid\ninput_grid = [\n    [1, 8, 8, 7, 7, 8],\n    [1, 1, 7, 7, 1, 8],\n    [7, 1, 1, 7, 7, 8]\n]\n\n# Transform the input grid\noutput_grid = solve(input_grid)\n\n# Print the output grid\nfor row in output_grid:\n    print(row)\n```\n\nThis code will replace all occurrences of `7` with `5` in the input grid."
        result = extract_code(text)
        self.assertIsNotNone(result)

class TestHistoryManager(TestCase):
    def test_log_works(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.close()
            log_file = Path(fp.name)
            history_manager = HistoryManager(log_file)
            with history_manager.start_new_message('user', 'gpt-4o'):
                history_manager.add_text('hi')
                history_manager.add_text('how are ya?')
                history_manager.add_image([[1]])
                history_manager.add_text('hi2')
            self.assertIn('how are ya?', log_file.read_text())
            log_file.unlink()

    def test_ttl_works(self):
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'gpt-4o', tst=1):
            history_manager.add_text('hi')
            history_manager.add_text('how are ya?')
            history_manager.add_image([[1]])
            history_manager.add_text('hi2')
        history_manager.set_ttl_last_elem(1)
        history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        history_manager.add_singletone_text_message('user', 'a prompt 2', 'gpt', tst=2)
        history_manager.set_ttl_last_pair(1, 1)
        self.assertEqual(len(history_manager.get_messages(cur_tst=None)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=1)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=2)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=3)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=4)), 0)

    
    def test_ttl_0_works(self):
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'gpt-4o', tst=1):
            history_manager.add_text('hi')
            history_manager.add_text('how are ya?')
            history_manager.add_image([[1]])
            history_manager.add_text('hi2')
        history_manager.set_ttl_last_elem(0)
        history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        history_manager.add_singletone_text_message('user', 'a prompt 2', 'gpt', tst=2)
        history_manager.set_ttl_last_pair(1, 1)
        self.assertEqual(len(history_manager.get_messages(cur_tst=None)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=1)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=2)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=3)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=4)), 0)

    def test_ttl_works_deeper_ttl(self):
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'gpt-4o', tst=1):
            history_manager.add_text('hi')
            history_manager.add_text('how are ya?')
            history_manager.add_image([[1]])
            history_manager.add_text('hi2')
        history_manager.set_ttl_last_elem(1)
        history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        history_manager.add_singletone_text_message('user', 'a prompt 2', 'gpt', tst=2)
        history_manager.set_ttl_last_pair(2, 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=None)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=1)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=2)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=3)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=4)), 2)
        self.assertEqual(len(history_manager.get_messages(cur_tst=5)), 0)

    def test_prune_images(self):
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'gpt-4o', tst=1):
            history_manager.add_text('hi')
            history_manager.add_text('how are ya?')
            history_manager.add_image([[1]])
            history_manager.add_text('hi2')
        history_manager.set_ttl_last_elem(1)
        history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        messages = LLMInterface().prune_images(messages)
        self.assertTrue(all(cont['type'] == 'text' for cont in messages[0]['content']))

class TestLiteLLMInterface(TestCase):
    def test_deepseek_with_litellm_deepseek(self):
        load_dotenv('.secrets', verbose=True)
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'deepseek/deepseek-reasoner', tst=1):
            history_manager.add_text('hi')
            history_manager.add_text('how are ya?')
        # history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='deepseek/deepseek-reasoner')
        print('chatting with llm')
        resp = llm_interface.chat_with_llm(messages, llm_tag=LLMInterface.TEXT)
        print(resp)
        self.assertEqual(len(resp) > 0)

    def test_deepseek_with_litellm_replicate(self):
        litellm.set_verbose=True
        load_dotenv('.secrets', verbose=True)
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'replicate/lucataco/deepseek-r1-70b:656b5ca19031ecadf6de648f81c7af84cba66eb7a1328fa863d0282a6fa7da7b', tst=1):
            history_manager.add_text('hi')
            # history_manager.add_text('how are ya?')
        # history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='replicate/lucataco/deepseek-r1-70b:656b5ca19031ecadf6de648f81c7af84cba66eb7a1328fa863d0282a6fa7da7b')
        print('chatting with llm')
        resp = llm_interface.chat_with_llm(messages, llm_tag=LLMInterface.TEXT)
        print(resp)
        self.assertTrue(len(resp) > 0)

    def test_deepseek_with_litellm_together(self):
        litellm.set_verbose=True
        load_dotenv('.secrets', verbose=True)
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'together_ai/deepseek-ai/DeepSeek-R1', tst=1):
            history_manager.add_text('hi')
            # history_manager.add_text('how are ya?')
        # history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='together_ai/deepseek-ai/DeepSeek-R1')
        print('chatting with llm')
        resp = llm_interface.chat_with_llm(messages, llm_tag=LLMInterface.TEXT)
        print(resp)
        self.assertTrue(len(resp) > 0)


    def test_deepseek_with_litellm_fireworks(self):
        litellm.set_verbose=True
        load_dotenv('.secrets', verbose=True)
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'fireworks/accounts/fireworks/models/deepseek-r1', tst=1):
            history_manager.add_text('hi')
            # history_manager.add_text('how are ya?')
        # history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='fireworks/accounts/fireworks/models/deepseek-r1')
        print('chatting with llm')
        resp = llm_interface.chat_with_llm(messages, llm_tag=LLMInterface.TEXT)
        print(resp)
        self.assertTrue(len(resp) > 0)

    def test_deepseek_and_openai(self):
        litellm.set_verbose=True
        load_dotenv('.secrets', verbose=True)
        history_manager = HistoryManager()
        with history_manager.start_new_message('user', 'replicate/lucataco/deepseek-r1-70b:656b5ca19031ecadf6de648f81c7af84cba66eb7a1328fa863d0282a6fa7da7b', tst=1):
            history_manager.add_text('hi')
            # history_manager.add_text('how are ya?')
        # history_manager.add_singletone_text_message('user', 'a prompt 1', 'gpt', tst=2)
        messages = history_manager.get_messages(cur_tst=None)
        llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='replicate/lucataco/deepseek-r1-70b:656b5ca19031ecadf6de648f81c7af84cba66eb7a1328fa863d0282a6fa7da7b')
        print('chatting with llm')
        resp = llm_interface.chat_with_llm(messages, llm_tag=LLMInterface.VISION)
        print(resp)
        self.assertTrue(len(resp) > 0)
            
if __name__ == '__main__':
    TestLiteLLMInterface().test_deepseek_with_litellm_fireworks()