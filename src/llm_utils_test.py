from unittest import TestCase

from llm_utils import extract_code


class testExtractCode(TestCase):
    def testExtractCode(self):
        text = "To address the issue, it seems the task is to replace the number `7` with `5`. Here's the corrected code:\n\n```python\ndef solve(input_grid):\n    # Transform the grid by replacing 7 with 5\n    output_grid = [\n        [5 if num == 7 else num for num in row]\n        for row in input_grid\n    ]\n    \n    return output_grid\n\n# Example input grid\ninput_grid = [\n    [1, 8, 8, 7, 7, 8],\n    [1, 1, 7, 7, 1, 8],\n    [7, 1, 1, 7, 7, 8]\n]\n\n# Transform the input grid\noutput_grid = solve(input_grid)\n\n# Print the output grid\nfor row in output_grid:\n    print(row)\n```\n\nThis code will replace all occurrences of `7` with `5` in the input grid."
        result = extract_code(text)
        self.assertIsNotNone(result)