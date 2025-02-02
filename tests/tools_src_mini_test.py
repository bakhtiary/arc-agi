import unittest

from dataset import LocalDataset
from tools_src_mini import YELLOW, get_linear_traversal_color_bunches, get_obj_colors_detailed, make_grid_monochrome, parse_grid_as_lines, parse_grid_as_objects, parsed_single_thing_to_str, describe_single_object_as_one_or_more_rectangulars, find_rectangle_in_positions_, get_filled_positions, get_rectangle_positions_, get_rectangles_ordered_by_area_, has_hole, parse_grid_as_objects_raw_flat, parsed_single_thing_to_str_json, parsed_things_to_str, parsed_things_to_str_json

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
    def test_6d75e8bb_hierarchical(self):
        dataset_, task_id_ = 'training', '6d75e8bb'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['output']
        objects = parse_grid_as_objects(grid, univalued=True, diagonal=False)
        self.assertEqual(objects, [{'obj': [((1, 4), 1)], 'size': 1, 'color': 'blue'}, {'obj': [((2, 0), 7)], 'size': 1, 'color': 'orange'}, {'obj': [((0, 2), 8), ((0, 1), 8)], 'size': 2, 'color': 'light_blue'}, {'obj': [((0, 5), 8), ((1, 5), 8), ((2, 5), 8)], 'size': 3, 'color': 'light_blue'}, {'obj': [((2, 1), 1), ((2, 2), 1), ((1, 0), 1), ((1, 1), 1), ((0, 0), 1)], 'size': 5, 'color': 'blue'}, {'obj': [((0, 3), 7), ((1, 2), 7), ((2, 4), 7), ((0, 4), 7), ((2, 3), 7), ((1, 3), 7)], 'size': 6, 'color': 'orange'}])
        self.assertEqual(parsed_single_thing_to_str(objects[0]), '(size=1, color="blue")')

    def test_c8f0f002_hierarchical(self):
        dataset_, task_id_ = 'training', 'c8f0f002'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objects = parse_grid_as_objects(grid, univalued=True, diagonal=False)
        self.assertEqual(objects, [{'obj': [((1, 4), 1)], 'size': 1, 'color': 'blue'}, {'obj': [((2, 0), 7)], 'size': 1, 'color': 'orange'}, {'obj': [((0, 2), 8), ((0, 1), 8)], 'size': 2, 'color': 'light_blue'}, {'obj': [((0, 5), 8), ((1, 5), 8), ((2, 5), 8)], 'size': 3, 'color': 'light_blue'}, {'obj': [((2, 1), 1), ((2, 2), 1), ((1, 0), 1), ((1, 1), 1), ((0, 0), 1)], 'size': 5, 'color': 'blue'}, {'obj': [((0, 3), 7), ((1, 2), 7), ((2, 4), 7), ((0, 4), 7), ((2, 3), 7), ((1, 3), 7)], 'size': 6, 'color': 'orange'}])
        self.assertEqual(parsed_single_thing_to_str(objects[0]), '(size=1, color="blue")')

    def test_c8f0f002_flat(self):
        dataset_, task_id_ = 'training', 'c8f0f002'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][0]['input']
        objects = parse_grid_as_objects(grid, univalued=True, diagonal=False, hierarchical=False)
        self.assertEqual(objects, [{'obj': [((2, 1), 1), ((2, 2), 1), ((1, 0), 1), ((1, 1), 1), ((0, 0), 1)], 'size': 5, 'color': 'blue'}, {'obj': [((0, 2), 8), ((0, 1), 8)], 'size': 2, 'color': 'light_blue'}, {'obj': [((0, 3), 7), ((1, 2), 7), ((2, 4), 7), ((0, 4), 7), ((2, 3), 7), ((1, 3), 7)], 'size': 6, 'color': 'orange'}, {'obj': [((0, 5), 8), ((1, 5), 8), ((2, 5), 8)], 'size': 3, 'color': 'light_blue'}, {'obj': [((1, 4), 1)], 'size': 1, 'color': 'blue'}, {'obj': [((2, 0), 7)], 'size': 1, 'color': 'orange'}])
        self.assertEqual(parsed_single_thing_to_str(objects[0]), '(size=5, color="blue")')

    def test_00dbd492_hierarchical(self):
        dataset_, task_id_ = 'evaluation', '00dbd492'
        task = LocalDataset(dataset_).read_task(task_id_)
        grid = task['train'][1]['input']
        objs = parse_grid_as_objects(grid, univalued=True, diagonal=True, hierarchical=True, object_describer='rectangulars/irregular:raw')
        descs_str = '\n'.join(parsed_single_thing_to_str(obj) for obj in objs)
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
        objs = parse_grid_as_objects(grid, univalued=True, diagonal=True, hierarchical=True, object_describer='rectangulars/irregular:raw')
        descs_str = '\n'.join(parsed_single_thing_to_str(obj) for obj in objs)
        print(descs_str)
        self.assertEqual(descs_str, '''(shape=rectangle, topleft_yx=(0, 0), height=2, width=19, color=grey, has_hole=False)
(shape=irregular, size=113, bounding_box=((9, 0), (14, 18)), color=light_blue, has_hole=True)
        (shape=point, position=(12, 9), color=black)
(shape=irregular, size=131, bounding_box=((2, 0), (8, 18)), color=yellow, has_hole=True)
        (shape=point, position=(3, 13), color=black)
        (shape=point, position=(5, 4), color=black)''')

class TestParsedSingleThingToStrJson(unittest.TestCase):
    def test_it_works(self):
        dataset_, task_id_ = 'training', '855e0971'
        task = LocalDataset(dataset_).read_task(task_id_)
        objs = parse_grid_as_objects(task['train'][0]['input'], univalued=True, diagonal=True, with_bg=True)
        self.assertEqual(parsed_single_thing_to_str_json(objs[0]), '{"size": 38, "color": "grey", "obj": "..."}')
        self.assertEqual(parsed_things_to_str_json(objs), '''[{"size": 38, "color": "grey", "obj": "..."},\n{"size": 113, "color": "light_blue", "obj": "...", "children": [{"size": 1, "color": "black", "obj": "..."}]},\n{"size": 131, "color": "yellow", "obj": "...", "children": [{"size": 1, "color": "black", "obj": "..."}, {"size": 1, "color": "black", "obj": "..."}]}]''')



class TestMakeGridMonochrome(unittest.TestCase):
    def test_it_works(self):
        grid = [[0,1,2]]
        self.assertEquals(make_grid_monochrome(grid, color_to_bg=0), [[0,YELLOW,YELLOW]])

    def test_two_rows(self):
        grid = [[0,1,2],[0,0,1]]
        self.assertEquals(make_grid_monochrome(grid, color_to_bg=0), [[0,YELLOW,YELLOW],[0,0,YELLOW]])

class TestParseGridAsLines(unittest.TestCase):
    def test_it_works_horizontal(self):
        grid = [[1,2,3]]
        lines = parse_grid_as_lines(grid, 'horizontal')
        a = parsed_things_to_str(lines)
        self.assertEqual(a, '(shape="line", direction="horizontal", y=0, start_x=0, end_x=2, length=3, colors="blue (len=1), red (len=1), green (len=1)")')

    def test_with_gap_horizontal(self):
        grid = [[1,2,3,0,4,5]]
        lines = parse_grid_as_lines(grid, 'horizontal', bg_color=0)
        a = parsed_things_to_str(lines)
        self.assertEqual(a, '(shape="line", direction="horizontal", y=0, start_x=0, end_x=2, length=3, colors="blue (len=1), red (len=1), green (len=1)")\n(shape="line", direction="horizontal", y=0, start_x=4, end_x=5, length=2, colors="yellow (len=1), grey (len=1)")')

    def test_it_works_vertical(self):
        grid = [[1],[2],[3]]
        lines = parse_grid_as_lines(grid, 'vertical')
        a = parsed_things_to_str(lines)
        self.assertEqual(a, '(shape="line", direction="vertical", x=0, start_y=0, end_y=2, length=3, colors="blue (len=1), red (len=1), green (len=1)")')

    def test_with_gap_vertical(self):
        grid = [[1],[2],[3],[0],[4],[5]]
        lines = parse_grid_as_lines(grid, 'vertical', bg_color=0)
        a = parsed_things_to_str(lines)
        self.assertEqual(a, '(shape="line", direction="vertical", x=0, start_y=0, end_y=2, length=3, colors="blue (len=1), red (len=1), green (len=1)")\n(shape="line", direction="vertical", x=0, start_y=4, end_y=5, length=2, colors="yellow (len=1), grey (len=1)")')

    def test_82819916(self):
        dataset_, task_id_ = 'training', '82819916'
        task = LocalDataset(dataset_).read_task(task_id_)
        lines = parse_grid_as_lines(task['train'][0]['input'], direction='horizontal')
        self.assertEqual(lines, [{'obj': [((1, 0), 3), ((1, 1), 3), ((1, 2), 2), ((1, 3), 3), ((1, 4), 3), ((1, 5), 2), ((1, 6), 3), ((1, 7), 3)], 'shape': 'line', 'direction': 'horizontal', 'y': 1, 'start_x': 0, 'end_x': 7, 'length': 8, 'colors': 'green (len=2), red (len=1), green (len=2), red (len=1), green (len=2)'}, {'obj': [((4, 0), 8), ((4, 1), 8), ((4, 2), 4)], 'shape': 'line', 'direction': 'horizontal', 'y': 4, 'start_x': 0, 'end_x': 2, 'length': 3, 'colors': 'light_blue (len=2), yellow (len=1)'}, {'obj': [((6, 0), 1), ((6, 1), 1), ((6, 2), 6)], 'shape': 'line', 'direction': 'horizontal', 'y': 6, 'start_x': 0, 'end_x': 2, 'length': 3, 'colors': 'blue (len=2), magenta (len=1)'}])
        

class TestGetLinearTraversalColorBunches(unittest.TestCase):
    def test_it_works(self):
        obj = [((1,1),1),((1,2),1),((1,3),3)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=1)')

    def test_unordered_line(self):
        obj = [((1,3),3),((1,2),1),((1,1),1)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=1)')

    def test_unordered_rectangle(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((3,2),2),((3,3),1),((2,1),1),((2,3),3),((3,1),1)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=2), blue (len=1), red (len=1), blue (len=2)')

    def test_unordered_open_semirectangle_at_tl(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((3,2),2),((3,3),1),((2,3),3),((3,1),1)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=2), blue (len=1), red (len=1), blue (len=1)')

    def test_unordered_open_semirectangle_at_somewhere_else_but_diagonally_connected(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((2,1),1),((3,2),2),((2,3),3),((3,1),1)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=2), red (len=1), blue (len=2)')

    def test_unordered_open_semirectangle_at_somewhere_else(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((2,1),1),((2,3),3),((3,1),1)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=3), green (len=2), blue (len=1)')

    def test_L_shaped(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((2,1),1),((3,1),4)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'green (len=1), blue (len=3), yellow (len=1)')

    def test_adjacent_lines(self):
        obj = [((1,3),3),((1,2),1),((1,1),1),((2,1),1), ((2,2),2)]
        b = get_obj_colors_detailed(obj)
        self.assertEqual(b['colors'], 'blue (len=2), green (len=1), red (len=1), blue (len=1)')


if __name__ == '__main__':
    # FIXME: these two lines
    # TestDescribeSingleObjectAsOneOrMoreRectangulars().test_solid_irregular_as_hlines()
    # TestParseGridAsLines().test_it_works()
    TestParsedSingleThingToStrJson().test_it_works()
    # TestParseGridAsObjects().test_c8f0f002_hierarchical()
    