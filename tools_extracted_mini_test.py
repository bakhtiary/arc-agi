import unittest

from tools_extracted_mini import get_grid_objects, has_hole

class TestGetObjects(unittest.TestCase):
    def test_simple(self):
        grid = [[0,0,0],[0,0,1],[0,0,0]]
        self.assertEqual(len(get_grid_objects(grid, univalued=True, diagonal=False, without_bg=True)), 1)
        self.assertEqual(len(get_grid_objects(grid, univalued=True, diagonal=False, without_bg=False)), 2)
        self.assertEqual(len(get_grid_objects(grid, univalued=False, diagonal=False, without_bg=True)), 1)
        self.assertEqual(len(get_grid_objects(grid, univalued=False, diagonal=False, without_bg=False)), 1)
    
class TestHasHole(unittest.TestCase):
    def test_simple_dash(self):
        grid = [[0,0,0],[0,0,1],[0,0,0]]
        objs = get_grid_objects(grid, univalued=True, diagonal=False, without_bg=True)
        self.assertFalse(has_hole(objs[0]))

    def test_hole_in_square(self):
        grid = [[0,1,1,1],[0,1,0,1],[0,1,1,1],[0,0,0,0]]
        objs = get_grid_objects(grid, univalued=True, diagonal=False, without_bg=True)
        self.assertTrue(has_hole(objs[0]))

if __name__ == '__main__':
    TestGetObjects().test_simple()
    TestHasHole().test_simple_dash()
    TestHasHole().test_hole_in_square()