import unittest
from unittest.mock import patch
from io import StringIO

from tool_writer_code_runner import CodeRunner


class ToolWriterCodeRunnerTest(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_we_can_run_code_directly_from_main(self, mock_stdout):
        code = '''from typing import List, Tuple\n\ndef identify_shapes(grid: List[List[int]]) -> List[List[Tuple[int, int, int]]]:\n    if not grid or not grid[0]:\n        return []\n\n    rows, cols = len(grid), len(grid[0])\n    visited = [[False for _ in range(cols)] for _ in range(rows)]\n    shapes = []\n\n    def dfs(x: int, y: int, color: int, shape: List[Tuple[int, int, int]]):\n        if x < 0 or x >= rows or y < 0 or y >= cols:\n            return\n        if visited[x][y] or grid[x][y] != color:\n            return\n\n        visited[x][y] = True\n        shape.append((x, y, color))\n\n        # Explore neighbors (up, down, left, right)\n        dfs(x - 1, y, color, shape)\n        dfs(x + 1, y, color, shape)\n        dfs(x, y - 1, color, shape)\n        dfs(x, y + 1, color, shape)\n\n    for i in range(rows):\n        for j in range(cols):\n            if not visited[i][j]:\n                shape = []\n                dfs(i, j, grid[i][j], shape)\n                if shape:\n                    shapes.append(shape)\n\n    return shapes\n\n# Test cases\ndef test_identify_shapes():\n    grid1 = [\n        [1, 1, 0, 0],\n        [1, 0, 0, 2],\n        [0, 0, 2, 2],\n        [3, 3, 3, 2]\n    ]\n    expected1 = [\n        [(0, 0, 1), (0, 1, 1), (1, 0, 1)],\n        [(0, 2, 0), (0, 3, 0), (1, 1, 0), (1, 2, 0), (2, 0, 0), (2, 1, 0)],\n        [(1, 3, 2), (2, 2, 2), (2, 3, 2), (3, 3, 2)],\n        [(3, 0, 3), (3, 1, 3), (3, 2, 3)]\n    ]\n\n    grid2 = [\n        [0, 0, 0],\n        [0, 1, 1],\n        [0, 1, 2]\n    ]\n    expected2 = [\n        [(0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 0, 0), (2, 0, 0)],\n        [(1, 1, 1), (1, 2, 1), (2, 1, 1)],\n        [(2, 2, 2)]\n    ]\n\n    assert identify_shapes(grid1) == expected1, "Test case 1 failed"\n    assert identify_shapes(grid2) == expected2, "Test case 2 failed"\n    print("All test cases passed!")\n\ntest_identify_shapes()\n'''
        CodeRunner().start_running(code=code)

        self.assertIn("The following error happened when evaluating your code", mock_stdout.getvalue().strip())

    # def test_we_can_run_code_in_a_separate_process(self):
    # --> ..._utils_test.test_we_can_run_code_from_chat_response