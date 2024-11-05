from unittest import TestCase

from dataset import LocalDataset
from grid_utils import get_grid_sizes

class testGetGridSizes(TestCase):
    def different_input_output_is_input(self):
        task = LocalDataset('training').read_task('c8f0f002')
        print(task['test'])
        print(get_grid_sizes(task, 'all'))

    def same_input_same_different_input(self):
        task = LocalDataset('training').read_task('a85d4709')
        print(task['test'])
        print(get_grid_sizes(task, 'all'))

    def same_input_same_different_input_which_0(self):
        task = LocalDataset('training').read_task('a85d4709')
        print(task['test'])
        print(get_grid_sizes(task, which=0))

if __name__ == '__main__':
    testGetGridSizes().different_input_output_is_input()
    testGetGridSizes().same_input_same_different_input()
    testGetGridSizes().same_input_same_different_input_which_0()
        