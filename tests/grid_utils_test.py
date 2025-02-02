import unittest

from dataset import LocalDataset
from grid_utils import get_grid_sizes, join_with_and

class TestJoinWithAnd(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(join_with_and([]), '')

    def test_1_elements_list(self):
        self.assertEqual(join_with_and(['a']), 'a')

    def test_2_elements_list(self):
        self.assertEqual(join_with_and(['a', 'b']), 'a and b')

    def test_n_elements_list(self):
        self.assertEqual(join_with_and(['a', 'b', 'c']), 'a, b, and c')

class TestGetGridSizes(unittest.TestCase):
    def test_different_input_output_is_input(self):
        task = LocalDataset('training').read_task('c8f0f002')
        print(task['test'])
        print(get_grid_sizes(task, 'all'))
        self.assertEqual(get_grid_sizes(task, 'all'), 'Sizes of displayed input images are 3x6, 3x4, and 3x5. Output image size is always the same as the input.')

    def test_same_input_same_different_input(self):
        task = LocalDataset('training').read_task('a85d4709')
        print(task['test'])
        print(get_grid_sizes(task, 'all'))
        self.assertEqual(get_grid_sizes(task, 'all'), 'All input sizes are the same 3x3. Output image size is always the same as the input.')

    def test_same_input_same_different_input_which_0(self):
        task = LocalDataset('training').read_task('a85d4709')
        print(task['test'])
        print(get_grid_sizes(task, which=0))
        self.assertEqual(get_grid_sizes(task, 'all'), 'All input sizes are the same 3x3. Output image size is always the same as the input.')

if __name__ == '__main__':
    TestGetGridSizes().different_input_output_is_input()
    TestGetGridSizes().same_input_same_different_input()
    TestGetGridSizes().same_input_same_different_input_which_0()
        