import unittest

from dataset import LocalDataset
from lens_orthogonal import desc_to_nested_str, describe_objects_orthogonal_flat, describe_objects_orthogonal_hierarchy
from tools_src_mini import get_grid_objects_as_flat_list, get_grid_objects_hierarchy


class TestDescribeObjectsOrthogonalFlat(unittest.TestCase):
    def grid_to_lens_str(self, grid, diagonal: bool):
        objs = get_grid_objects_as_flat_list(grid, univalued=True, diagonal=diagonal, with_bg=True)
        descs = describe_objects_orthogonal_flat(objs, univalued=True)
        descs_str = '\n'.join(desc_to_nested_str(desc) for desc in descs)
        return descs_str

    def grids_to_lens_str(self, diagonal: bool):
        result = ''
        for i, sample in enumerate(self.task['train'], 1):
            result += f'## Train pair {i}'
            result += self.grid_to_lens_str(sample['input'], diagonal=diagonal)
            result += self.grid_to_lens_str(sample['output'], diagonal=diagonal)
            result += '\n'

        for i, sample in enumerate(self.task['test'], 1):
            result += f'## Test pair {i}'
            result += self.grid_to_lens_str(sample['input'], diagonal=diagonal)
            result += '\n'

        return result
    
    def test_72322fa7(self):
        dataset_, task_id_ = 'training', '72322fa7'
        self.task = LocalDataset(dataset_).read_task(task_id_)
        result = self.grids_to_lens_str(diagonal=True)
        self.assertIsNotNone(result)

    def test_00dbd492(self):
        dataset_, task_id_ = 'evaluation', '00dbd492'
        self.task = LocalDataset(dataset_).read_task(task_id_)
        result = self.grids_to_lens_str(diagonal=True)
        self.assertIsNotNone(result)


class TestDescribeObjectsOrthogonalHierarchy(unittest.TestCase):
    def test_00dbd492_hierarchy(self):
        dataset_, task_id_ = 'evaluation', '00dbd492'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][1]['input']
        objs5 = get_grid_objects_hierarchy(grid, univalued=True, diagonal=True)
        desc5 = describe_objects_orthogonal_hierarchy(objs5, univalued=True)
        self.assertEqual(desc5, [{'shape': 'rectangle', 'topleft_yx': (0, 0), 'width': 7, 'height': 7, 'thickness': 1, 'color': 'red', 'has_hole': True, 'children': [{'shape': 'rectangle', 'topleft_yx': (1, 1), 'width': 5, 'height': 5, 'thickness': 2, 'color': 'black', 'has_hole': True, 'children': [{'shape': 'point', 'position': (3, 3), 'color': 'red'}]}]}, {'shape': 'irregular', 'size': 32, 'color': 'black', 'has_hole': False}])


    def test_855e0971_hierarchy(self):
        dataset_, task_id_ = 'training', '855e0971'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objs5 = get_grid_objects_hierarchy(grid, univalued=True, diagonal=True, with_bg=True)
        desc5 = describe_objects_orthogonal_hierarchy(objs5, univalued=True)
        self.assertEqual(desc5, [{'shape': 'rectangle', 'topleft_yx': (0, 0), 'height': 2, 'width': 19, 'color': 'grey', 'has_hole': False}, {'shape': 'irregular', 'size': 113, 'bounding_box': ((9, 0), (14, 18)), 'color': 'light_blue', 'has_hole': True, 'children': [{'shape': 'point', 'position': (12, 9), 'color': 'black'}]}, {'shape': 'irregular', 'size': 131, 'bounding_box': ((2, 0), (8, 18)), 'color': 'yellow', 'has_hole': True, 'children': [{'shape': 'point', 'position': (3, 13), 'color': 'black'}, {'shape': 'point', 'position': (5, 4), 'color': 'black'}]}])