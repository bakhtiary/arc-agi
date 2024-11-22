from pathlib import Path
import tempfile
from unittest import TestCase

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
        self.assertEqual(len(history_manager.get_messages(cur_tst=1)), 3)
        self.assertEqual(len(history_manager.get_messages(cur_tst=2)), 3)
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
            
