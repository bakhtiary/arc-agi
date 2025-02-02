

import unittest

from dataset import LocalDataset
from simple_state_machine_with_tools_and_lens_3 import SimpleStateMachineWithToolsAndLens3
from simple_state_machine_with_tools_and_lens_4 import SimpleStateMachineWithToolsAndLens4


class SimpleStateMachineWithToolsAndLens3Test(unittest.TestCase):
    def test_send_descriptors_works(self):
        sm = SimpleStateMachineWithToolsAndLens3('82819916', LocalDataset('training'))
        result = sm.send_descriptors()
        self.assertIsNotNone(result)

    def test_select_descriptor(self):
        sm = SimpleStateMachineWithToolsAndLens3('82819916', LocalDataset('training'))
        sm.select_descriptor('''After analyzing the available descriptors and considering the task of mapping colors (specifically replacing orange with gray), the **"objects/orthogonal/rectangulars/irregular:raw"** descriptor is the most suitable choice. This descriptor provides detailed information about the shapes, their positions, and colors, which is essential for accurately identifying and modifying the specified colors in the grid.

```json
{
  "chosen_descriptor": "objects/orthogonal-without-bg/rectangulars/irregular:raw",
  "monochromatic_useful": false,
  "monochromatic_bg": null,
  "other_useful_descriptors": ""
}
```''')
        self.assertIsNotNone(sm.default_input_grid_lens)


class SimpleStateMachineWithToolsAndLens4Test(unittest.TestCase):
    def test_send_all_pairs_with_descriptors_True(self):
        sm = SimpleStateMachineWithToolsAndLens4('82819916', LocalDataset('training'))
        sm.select_descriptor('''After analyzing the available descriptors and considering the task of mapping colors (specifically replacing orange with gray), the **"objects/orthogonal/rectangulars/irregular:raw"** descriptor is the most suitable choice. This descriptor provides detailed information about the shapes, their positions, and colors, which is essential for accurately identifying and modifying the specified colors in the grid.

```json
{
  "chosen_descriptor": "objects/orthogonal-without-bg/rectangulars/irregular:raw",
  "monochromatic_useful": false,
  "monochromatic_bg": null,
  "other_useful_descriptors": ""
}
```''')
        result = sm.send_all_pairs(with_descriptors=True)
        self.assertIsNotNone(result)

    def test_hlines(self):
        local_dataset = LocalDataset('training')
        sm = SimpleStateMachineWithToolsAndLens4('82819916', local_dataset)
        # for pair_i, pair in enumerate(local_dataset.read_task('82819916')['train']):
        #   print(pair_i)
        sm.grid_to_lens_str_json(local_dataset.read_task('82819916')['train'][0]['input'], parse_type='hlines')


if __name__ == '__main__':
    SimpleStateMachineWithToolsAndLens4Test().test_hlines()