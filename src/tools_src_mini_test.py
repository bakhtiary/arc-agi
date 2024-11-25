import unittest

from dataset import LocalDataset
from tools_src_mini import parse_grid_as_objects, parsed_to_nested_str, describe_single_object_as_one_or_more_rectangulars, find_rectangle_in_positions_, get_filled_positions, get_rectangle_positions_, get_rectangles_ordered_by_area_, has_hole, parse_grid_as_objects_raw_flat

class TestParseGridAsObjectsRawFlat(unittest.TestCase):
    def test_simple(self):
        grid = [[0,0,0],[0,0,1],[0,0,0]]
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=True)), 2)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)), 1)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=True)), 1)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=False, bg_color=0)), 1)        

    def test_855e0971(self):
        # first pair input
        grid = [[5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 0, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8], [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]]
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=True, bg_color=0)), 6)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)), 3)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=True, bg_color=0)), 1)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=False, bg_color=0)), 1)

    def test_72322fa7(self):
        dataset_, task_id_ = 'training', '72322fa7'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        # test diagonal=False
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=True, bg_color=0)), 19)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)), 17)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=True, bg_color=0)), 1)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=False, with_bg=False, bg_color=0)), 13)

        # test diagonal=True
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=True, with_bg=True, bg_color=0)), 12)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=True, with_bg=False, bg_color=0)), 11)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=True, with_bg=True, bg_color=0)), 1)
        self.assertEqual(len(parse_grid_as_objects_raw_flat(grid, univalued=False, diagonal=True, with_bg=False, bg_color=0)), 6)
    
class TestHasHole(unittest.TestCase):
    def test_simple_dash(self):
        grid = [[0,0,0],[0,0,1],[0,0,0]]
        objs = parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)
        self.assertFalse(has_hole(objs[0]))

    def test_hole_in_square(self):
        grid = [[0,1,1,1],[0,1,0,1],[0,1,1,1],[0,0,0,0]]
        objs = parse_grid_as_objects_raw_flat(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)
        self.assertTrue(has_hole(objs[0]))

class GetRectanglesOrderedByArea(unittest.TestCase):
    def test_it_works(self):
        self.assertEqual(list(get_rectangles_ordered_by_area_(4,4)), [(4, 4), (3, 4), (4, 3), (3, 3), (2, 4), (4, 2), (2, 3), (3, 2), (1, 4), (2, 2), (4, 1), (1, 3), (3, 1), (1, 2), (2, 1), (1, 1)])

class TestGetRectanglePositions(unittest.TestCase):
    def test_it_works(self):
        self.assertEqual(get_rectangle_positions_(tl_y=2,tl_x=1,w=3,h=4,t=1),
            [(2, 1), (2, 2), (2, 3), (3, 1), (3, 3), (4, 1), (4, 3), (5, 1), (5, 2), (5, 3)])
        self.assertEqual(len(get_rectangle_positions_(2,2,4,5,2)), 20)
        self.assertEqual(len(get_rectangle_positions_(2,2,5,5,2)), 25 - 1)
    
    def test_too_thick(self):
        with self.assertRaises(ValueError):
            get_rectangle_positions_(1,1,3,3,2)

    def test_point(self):
        self.assertEqual(get_rectangle_positions_(10,11,1,1,1), [(10,11)])

    def test_line(self):
        self.assertEqual(get_rectangle_positions_(10,11,1,3,1), [(10,11),(11,11),(12,11)])

    def test_thickness_2(self):
        self.assertEqual(len(get_rectangle_positions_(1,1,5,5,2)), 24)

class TestFindRectangleInPositions(unittest.TestCase):
    def test_it_works(self):
        positions = [(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)]
        rect = find_rectangle_in_positions_(set(positions))
        expected = dict(shape='rectangle', positions=positions, w=3, h=3, tl_x=0, tl_y=0, thickness=1)
        self.assertEqual(set(rect['positions']), set(positions))
        expected['positions'] = rect['positions']
        self.assertEqual(rect, expected)

    def test_thicker(self):
        grid = [[1,1,1,1,1],
                [1,1,1,1,1],
                [1,1,0,1,1],
                [1,1,1,1,1],
                [1,1,1,1,1]]
        positions = [(y,x) for y in range(len(grid)) for x in range(len(grid[0])) if grid[y][x] == 1]
        rect = find_rectangle_in_positions_(set(positions))
        expected = dict(shape='rectangle', positions=positions, w=5, h=5, tl_x=0, tl_y=0, thickness=2)
        self.assertEqual(set(rect['positions']), set(positions))
        expected['positions'] = rect['positions']
        self.assertEqual(rect, expected)
    
    def test_filled(self):
        positions = [(0,0),(0,1),(1,0),(1,1)]
        rect = find_rectangle_in_positions_(set(positions))
        expected = dict(shape='rectangle', positions=positions, w=2, h=2, tl_x=0, tl_y=0, thickness=0)
        self.assertEqual(set(rect['positions']), set(positions))
        expected['positions'] = rect['positions']
        self.assertEqual(rect, expected)

    def test_filled_translated(self):
        positions = [(1,1),(1,2),(1,3),(2,1),(2,2),(2,3),(3,1),(3,2),(3,3)]
        rect = find_rectangle_in_positions_(set(positions))
        expected = dict(shape='rectangle', positions=positions, w=3, h=3, tl_x=1, tl_y=1, thickness=0)
        self.assertEqual(set(rect['positions']), set(positions))
        expected['positions'] = rect['positions']
        self.assertEqual(rect, expected)
        

class TestGetFilledPositions(unittest.TestCase):
    def test_it_works(self):
        positions = [(1, 2), (2, 1), (3, 1), (1, 1), (2, 3), (3, 3), (3, 2), (1, 3)]
        obj = [(pos, 0) for pos in positions]
        self.assertEqual(set(get_filled_positions(obj)), set(positions + [(2,2)]))

class TestDescribeSingleObjectAsOneOrMoreRectangulars(unittest.TestCase):
    def test_thikness_1(self):
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3,3)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj)
        print(ret)
        self.assertEqual(ret['thickness'], 1)

    def test_solid_square(self):
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2,2), (2, 3), (3, 1), (3, 2), (3,3)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj)
        print(ret)
        with self.assertRaises(KeyError):
            x = ret['thickness']

    def test_solid_rectangle(self):
        positions = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj)
        print(ret)
        self.assertEqual(ret, {'shape': 'rectangle', 'topleft_yx': (1, 1), 'height': 3, 'width': 2, 'colors': 'black', 'has_hole': False})
        self.assertFalse('thickness' in ret)

    def test_solid_irregular(self):
        positions = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (3,3)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj)
        print(ret)
        self.assertEqual(ret, {'shape': 'irregular', 'size': 7, 'bounding_box': ((1, 1), (3, 3)), 'color': 'black', 'has_hole': False})
        
    def test_solid_irregular_as_rectangles(self):
        positions = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (3,3)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj, irregular_method='rectangles')
        print(ret)
        self.assertEqual(ret, {'shape': 'irregular', 'size': 7, 'bounding_box': ((1, 1), (3, 3)), 'color': 'black', 'has_hole': False, 'as_rectangles': [{'shape': 'rectangle', 'topleft_yx': (1, 1), 'height': 3, 'width': 2, 'thickness': 1, 'color': 'black', 'has_hole': False}, {'shape': 'point', 'position': (3, 3), 'color': 'black'}]})

    def test_solid_irregular_as_hlines(self):
        positions = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (3,3)]
        obj = [(pos, 0) for pos in positions]
        ret = describe_single_object_as_one_or_more_rectangulars(obj, irregular_method='hlines')
        print(ret)
        #self.assertEqual(ret, {'shape': 'irregular', 'size': 7, 'bounding_box': ((1, 1), (3, 3)), 'color': 'black', 'has_hole': False, 'as_rectangles': [{'shape': 'rectangle', 'topleft_yx': (1, 1), 'height': 3, 'width': 2, 'thickness': 1, 'color': 'black', 'has_hole': False}, {'shape': 'point', 'position': (3, 3), 'color': 'black'}]})
        

class TestParseGridAsObjects(unittest.TestCase):
    
    def test_c8f0f002_hierarchical(self):
        dataset_, task_id_ = 'training', 'c8f0f002'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objects = parse_grid_as_objects(grid, univalued=True, diagonal=False)
        self.assertEqual(objects, [{'obj': [((1, 4), 1)], 'size': 1, 'color': 'blue'}, {'obj': [((2, 0), 7)], 'size': 1, 'color': 'orange'}, {'obj': [((0, 2), 8), ((0, 1), 8)], 'size': 2, 'color': 'light_blue'}, {'obj': [((0, 5), 8), ((1, 5), 8), ((2, 5), 8)], 'size': 3, 'color': 'light_blue'}, {'obj': [((2, 1), 1), ((2, 2), 1), ((1, 0), 1), ((1, 1), 1), ((0, 0), 1)], 'size': 5, 'color': 'blue'}, {'obj': [((0, 3), 7), ((1, 2), 7), ((2, 4), 7), ((0, 4), 7), ((2, 3), 7), ((1, 3), 7)], 'size': 6, 'color': 'orange'}])
        self.assertEqual(parsed_to_nested_str(objects[0]), '(size=1, color="blue")')

    def test_c8f0f002_flat(self):
        dataset_, task_id_ = 'training', 'c8f0f002'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objects = parse_grid_as_objects(grid, univalued=True, diagonal=False, hierarchical=False)
        self.assertEqual(objects, [{'obj': [((2, 1), 1), ((2, 2), 1), ((1, 0), 1), ((1, 1), 1), ((0, 0), 1)], 'size': 5, 'color': 'blue'}, {'obj': [((0, 2), 8), ((0, 1), 8)], 'size': 2, 'color': 'light_blue'}, {'obj': [((0, 3), 7), ((1, 2), 7), ((2, 4), 7), ((0, 4), 7), ((2, 3), 7), ((1, 3), 7)], 'size': 6, 'color': 'orange'}, {'obj': [((0, 5), 8), ((1, 5), 8), ((2, 5), 8)], 'size': 3, 'color': 'light_blue'}, {'obj': [((1, 4), 1)], 'size': 1, 'color': 'blue'}, {'obj': [((2, 0), 7)], 'size': 1, 'color': 'orange'}])
        self.assertEqual(parsed_to_nested_str(objects[0]), '(size=5, color="blue")')

    def test_00dbd492_hierarchical(self):
        dataset_, task_id_ = 'evaluation', '00dbd492'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][1]['input']
        objs = parse_grid_as_objects(grid, univalued=True, diagonal=True, hierarchical=True, object_describer='rectangular/irregular:raw')
        descs_str = '\n'.join(parsed_to_nested_str(obj) for obj in objs)
        print(descs_str)
        self.maxDiff=None
        self.assertEqual(descs_str, '''(shape=rectangle, topleft_yx=(0, 0), height=7, width=7, thickness=1, color=red, has_hole=True)
        (shape=rectangle, topleft_yx=(1, 1), height=5, width=5, thickness=2, color=black, has_hole=True)
                (shape=point, position=(3, 3), color=red)
(shape=irregular, size=32, bounding_box=((0, 0), (8, 8)), color=black, has_hole=False)''')


    def test_855e0971_hierarchical(self):
        dataset_, task_id_ = 'training', '855e0971'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objs = parse_grid_as_objects(grid, univalued=True, diagonal=True, hierarchical=True, object_describer='rectangular/irregular:raw')
        descs_str = '\n'.join(parsed_to_nested_str(obj) for obj in objs)
        print(descs_str)
        self.assertEqual(descs_str, '''(shape=rectangle, topleft_yx=(0, 0), height=2, width=19, color=grey, has_hole=False)
(shape=irregular, size=113, bounding_box=((9, 0), (14, 18)), color=light_blue, has_hole=True)
        (shape=point, position=(12, 9), color=black)
(shape=irregular, size=131, bounding_box=((2, 0), (8, 18)), color=yellow, has_hole=True)
        (shape=point, position=(3, 13), color=black)
        (shape=point, position=(5, 4), color=black)''')


class TestParseGridAsLines(unittest.TestCase):
    ...

if __name__ == '__main__':
    # FIXME: these two lines
    # TestDescribeSingleObjectAsOneOrMoreRectangulars().test_solid_irregular_as_hlines()
    # TestParseGridAsLines().test_it_works()
    
    TestParseGridAsObjects().test_c8f0f002_hierarchical()