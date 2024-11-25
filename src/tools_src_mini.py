## flood fill, connect lines, describe shapes (with discribe inside, but about unconnected shapes with an "invisible" tie, or
# black squares on a large yellow rectangle)
from collections import defaultdict
import functools
from typing import Literal

import numpy as np
from code_utils import ignore_for_llm_tools_docs, llm_action_tool, llm_lense_tool, llm_tool
from collections import deque

############################
# types and constants
Grid = list[list[int]]
Object = list[tuple[tuple[int,int], int]]
ObjectDict_ = dict
Indices = list[tuple[int,int]]

BLACK=0
BLUE=1
RED=2
GREEN=3
YELLOW=4
GREY=5
MAGENTA=6
ORANGE=7
LIGHT_BLUE=8
BROWN=9

# will be excluded from documentation, because of the trailing underline
OBJ_ = 0
GRID_ = 1
color_to_str_dict_ = {
    BLACK: "black",
    BLUE: "blue",
    RED: "red",
    GREEN: "green",
    YELLOW: "yellow",
    GREY: "grey",
    MAGENTA: "magenta",
    ORANGE: "orange",
    LIGHT_BLUE: "light_blue",
    BROWN: "brown"
}

############################
# utils
def obj_func_cacher(func):
    cache_ = dict()
    def _wrapper(obj: Object):
        obj_as_set = frozenset(obj)
        if obj_as_set not in cache_:
            cache_[obj_as_set] = func(obj)
        return cache_[obj_as_set]
    return _wrapper

def bounding_box_(obj: Object) -> tuple[tuple[int,int],tuple[int,int]]:
    """ Returns ((tl_y,tl_x),(br_y,br_x)) where t/b is for top/bottom and r/l for right/left """
    if isinstance(obj, dict):
        obj = obj['obj']
    positions = set(pos for pos, _ in obj)
    xs = [x for y, x in positions]
    ys = [y for y, x in positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    return ((min_y, min_x), (max_y, max_x))


def dict_to_str(d: dict) -> str:
    kvs = []
    for k,v in d.items():
        if isinstance(v, str):
            kvs.append(f'{k}="{v}"')
        else:
            kvs.append(f'{k}={v}')

    return '(' + ", ".join(kvs) + ')'

def parsed_to_nested_str(d: dict, obj_key: bool=False, indent=0) -> str:
    result = ''
    children = []
    if 'children' in d:
        children = d['children']
        del d['children']
    d = {k: v for k,v in d.items() if (obj_key or k != 'obj')}
    result += ' ' * 8 * indent + dict_to_str(d)
    for child in children:
        result += '\n' + parsed_to_nested_str(child, obj_key, indent+1)        
    return result

############################
# simple tools
@llm_tool
def direct_neighbors(loc: tuple[int,int]) -> Indices:
    """ directly adjacent indices (including invalid (negative) indiced) """
    return list(set({(loc[0] - 1, loc[1]), (loc[0] + 1, loc[1]), (loc[0], loc[1] - 1), (loc[0], loc[1] + 1)}))

@llm_tool
def diagonal_neighbors(loc: tuple[int,int]) -> Indices:
    """ diagonally adjacent indices (including invalid (negative) indiced) """
    return list(set({(loc[0] - 1, loc[1] - 1), (loc[0] - 1, loc[1] + 1), (loc[0] + 1, loc[1] - 1), (loc[0] + 1, loc[1] + 1)}))

@llm_tool
def neighbors(loc: tuple[int,int]) -> Indices:
    """ adjacent indices (including invalid (negative) indiced) """
    return list(set(direct_neighbors(loc)) | set(diagonal_neighbors(loc)))

def grid_or_object(element: Object|Grid) -> int:
    if isinstance(element, dict):
        element = element['obj']
    if isinstance(element[0], tuple):
        return OBJ_
    else:
        return GRID_

@llm_tool
def most_common_color(element: Object|Grid) -> int:
    """ most common color in an object or a grid """
    if isinstance(element, dict):
        element = element['obj']
    if grid_or_object(element) == OBJ_:
        values = [x[1] for x in element]
    else:
        values = [cell for row in element for cell in row]
    return max(set(values), key=values.count)

@llm_tool
def get_obj_colors(obj: Object) -> set[int]:
    """ colors in an object """
    if isinstance(obj, dict):
        obj = obj['obj']
    colors = [color for _, color in obj]
    return set(colors)

@llm_tool #?
def obj_to_univalued(obj: Object, uni_color=0):
   if isinstance(obj, dict):
        obj = obj['obj']
   return [(pos, uni_color) for pos, _ in obj]

@llm_tool #?
def get_subobject(obj: Object, positions: dict):
    if isinstance(obj, dict):
        obj = obj['obj']
    positions = dict.fromkeys(positions)
    return [(x,c) for x,c in obj if x in positions]


############################
# hole and fill functions
def has_hole(obj: Object):    
    """ Determine if the object has a hole."""
    if isinstance(obj, dict):
        obj = obj['obj']
    # return len(get_hole_points(obj)) != 0
    min_y, min_x, w, h, grid, visited = get_grid_and_visited_for_hole_functions_(obj)
    for y in range(h):
        for x in range(w):
            if grid[y][x] == 0 and not visited[y][x]:
                return True  # Hole detected

    return False

@llm_action_tool
def flood_fill(obj: Object, color: int) -> Object:
    if isinstance(obj, dict):
        obj = obj['obj']
    return obj + [(pos, color) for pos in get_hole_positions(obj)]

@llm_tool
def get_hole_positions(obj: Object) -> Indices:
    if isinstance(obj, dict):
        obj = obj['obj']
    min_y, min_x, w, h, grid, visited = get_grid_and_visited_for_hole_functions_(obj)
    return list((min_y + y, min_x + x) for y in range(h) for x in range(w) if grid[y][x] == 0 and not visited[y][x])

# @llm_tool
def get_filled_positions(obj: Object) -> Indices:
    if isinstance(obj, dict):
        obj = obj['obj']
    return list(pos for pos, _ in obj) + get_hole_positions(obj)
          
# @ignore_for_llm_tools_docs
@obj_func_cacher
def get_grid_and_visited_for_hole_functions_(obj: Object):
    # if isinstance(obj, dict):
    #    obj = obj['obj']
    positions = set(pos for pos, _ in obj)
    xs = [x for y, x in positions]
    ys = [y for y, x in positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    w, h = max_x - min_x + 1, max_y - min_y + 1
    
    grid = [[0 for _ in range(w)] for _ in range(h)]

    for (y, x) in positions:
        grid[y - min_y][x - min_x] = 1

    visited = [[False for _ in range(w)] for _ in range(h)]
    queue = deque()

    for y in range(h):
        for x in range(w):
            if (y == 0 or y == h - 1 or x == 0 or x == w - 1) and grid[y][x] == 0:
                queue.append((y, x))
                visited[y][x] = True

    while queue:
        y, x = queue.popleft()
        for ni, nj in [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]:
            if 0 <= ni < h and 0 <= nj < w and grid[ni][nj] == 0 and not visited[ni][nj]:
                queue.append((ni, nj))
                visited[ni][nj] = True
    
    return  min_y, min_x, w, h, grid, visited

############################
# Top level grid lenses: (1) describe as objects (flat/hierarchical, raw/rectangular/rectangular+)
@llm_tool
def parse_grid_as_objects(grid: Grid,
    univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None,
    hierarchical: bool=True,
    object_describer: Literal['raw','rectangular/irregular:raw','rectangular/irregular:rectangles','rectangular/irregular:vlines', 'rectangular/irregular:hlines', 'vlines', 'hlines']='raw'
) -> list[dict]:
    """ Extract connected objects from a grid.

    Args:
        grid (List[List[int]]): A 2D grid represented as a list of lists of integers.
        univalued (bool): If True, only consider connected cells with the same value as part of an object.
                          If False, any non-background value is included in the object.
        diagonal (bool): If True, include diagonal neighbors when determining connectivity.
                         If False, only consider orthogonal neighbors (up, down, left, right).
        with_bg (bool): If True, considers the background value, when finding objects and background cells might be part of the objects returned.
            (Note: when univalued is True, with_bg leads to include univalued background patches)
        bg_color (int): Specifies the background color in the grid to be used with `with_bg`=False.
        hierarchical (bool): If True, an object that encloses other objects will have a `children` key that lists the objects.
        object_describer (str): If `raw`, each object is retuend as a dictionary with `obj` key and object points as a list[tuple[tuple[int,int],int]] as the list of ((y,x),color) tuples with no further description.
                            If `rectangular/irregular:X`, try to parse each object as a single rectangular object; For each object, besides `obj`, there is a `shape` key that can be `point`, `line` (for horizontal or vertical lines), `rectangle` (for solid or hollow straight rectangles), or `irregular` (all other objects, such as titlted lines, polylines, triangles, L-shapes, circles, and even rectangles with an attached protrusion, etc). Each shape has additional relevant keys as given in the examples below.
                            X is not `raw` is used to parse an irregular shape further, as a set of rectangular objects (starting from the largest ones), vertical, or horlizontal objects in `as-X` key.
                            If  `vlines` or `hilnes`, parses each object as a set of vertical or horizontal lines.
    Returns:
        list[dict]: A list of dicts. Each dict has at least `obj` key for the object's list of ((row-index, column-index), color) tuples. It may also contain a `children` key as described above.
    
    Note 1:
        univalued=True, with_bg=True --> all univalued objects, including background patches (so, bg_color is not needed)
        univalued=True, with_bg=False -->  all univalued objects other than background patches
        univalued=False, with_bg=True -->  the grid as a single object (so, bg_color is not needed)
        univalued=False, with_bg=False -->  all colored objects seperated by background

    Note 2:
        Please specify `bg_color` with `with_bg=False`

    Note 3: Examples
        Example objects for different shapes when `describe_method='rectangular'` or `describe_method='rectangular+'`:
            - Ponit: {{'shape': 'point', 'position': (y, x), 'color': 'red'}}
            - Line: {{'shape': 'line', 'direction': 'vertical', 'x': first_pos[1], 'start_y': 5, 'length': 6, 'colors': 'red,blue'}}
            - Rectangle: {{'shape': 'rectangle', 'topleft_yx': (1, 1), 'width': 5, 'height': 5, 'thickness': 2, 'color': 'black', 'has_hole': True}}
            - Irregular with `describe_method='rectangular'`:: {{'shape': 'irregular', 'size': 10, color='blue', 'bounding_box': ((tl-y,tl-x),(br-y,br-x)), 'has_hole': False}}
            - Irregular with `describe_method='rectangular+'`:: {{'shape': 'irregular', 'size': 10, color='blue', 'bounding_box': ((tl-y,tl-x),(br-y,br-x)), 'has_hole': False}}
        
        If a rectangle or irregular shape is solid, `has_hole` will be `False` and no `thickness` (for rectangles) is present.
        If the object is not univalued, instead of the `color` key, there will be a `colors` key with comma-seperated list of unique colors in the shape.
    """
    assert object_describer in ['raw','rectangular/irregular:raw','rectangular/irregular:rectangles','rectangular/irregular:vlines', 'rectangular/irregular:hlines', 'vlines', 'hlines']

    if not hierarchical:
        objs = parse_grid_as_objects_raw_flat(grid, univalued, diagonal, with_bg, bg_color)
        objs = [{'obj': obj} for obj in objs]
    else:
        objs = parse_grid_as_objects_raw_hierarchal(grid, univalued, diagonal, with_bg, bg_color)

    def add_description_to_obj_(obj: dict):
        if object_describer == 'raw':
            obj['size'] = len(obj['obj'])
            obj.update(get_color_dict(obj['obj']))
            return obj
        if object_describer in ['rectangular/irregular:raw','rectangular/irregular:rectangles','rectangular/irregular:vlines', 'rectangular/irregular:hlines']:
            irregular_method = object_describer.removeprefix('rectangular/irregular:')
            result = describe_single_object_as_one_or_more_rectangulars(obj['obj'], irregular_method=irregular_method)
            obj.update(result)
        elif object_describer in ['vlines', 'hlines']:
            result = describe_single_object_as_one_or_more_lines(obj['obj'], direction='vertical' if object_describer=='vlines' else 'horizontal')
            obj[f'as_{object_describer}'] = result
        children = []
        if 'children' in obj:
            for child_obj in obj['children']:
                children.append(add_description_to_obj_(child_obj))
            obj['children'] = children
        return obj
    
    for obj in objs:
        add_description_to_obj_(obj)
    
    return objs


def parse_grid_as_objects_raw_flat(grid: Grid, univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None) -> list[Object]:
    if not with_bg and bg_color is None:
        raise ValueError('Please specify `bg_color` with `with_bg=False`.')

    objs = []
    occupied = set()
    h, w = len(grid), len(grid[0])
    unvisited = list((i, j) for i in range(len(grid)) for j in range(len(grid[0])))
    diag_fun = neighbors if diagonal else direct_neighbors
    for loc in unvisited:
        if loc in occupied:
            continue
        val = grid[loc[0]][loc[1]]
        if not with_bg and val == bg_color:
            continue
        obj = {(loc, val)}
        cands = {loc}
        while len(cands) > 0:
            neighborhood = set()
            for cand in cands:
                v = grid[cand[0]][cand[1]]
                if (univalued and val == v) or (not univalued and (with_bg or v != bg_color)):
                    obj.add((cand, v))
                    occupied.add(cand)
                    neighborhood |= {
                        (y, x) for y, x in diag_fun(cand) if 0 <= y < h and 0 <= x < w
                    }
            cands = neighborhood - occupied
        objs.append(list(obj))
    return objs


def parse_grid_as_objects_raw_hierarchal(grid: Grid, univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None) -> list[dict]:
    if not with_bg and bg_color is None:
        raise ValueError('Please specify `bg_color` with `with_bg=False`.')
   
    objs = parse_grid_as_objects_raw_flat(grid, univalued, diagonal, with_bg, bg_color)
    
    def enclosing_grid_area(obj):
        positions = set(pos for pos, _ in obj)
        xs = [x for y, x in positions]
        ys = [y for y, x in positions]
        min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
        w, h = max_x - min_x + 1, max_y - min_y + 1
        return w*h
        
    objs = [{'obj': obj} for obj in sorted(objs, key=enclosing_grid_area)]
    filled_dict = dict()
    for i, obj in enumerate(objs):
        filled_dict[i] = set(get_filled_positions(obj['obj']))

    for i in range(len(objs)):
        for j in range(len(objs)):
            if filled_dict[i] < filled_dict[j]:
                if 'parent' in objs[i]:
                    continue
                
                objs[i]['parent'] = j
                if 'children' not in objs[j]:
                    objs[j]['children'] = []
                objs[j]['children'].append(i)
                

    roots = [obj for obj in objs if 'parent' not in obj]
    for obj in objs:
        if 'parent' in obj:
            del obj['parent']

    def _set_children_objs(obj: dict):
        if 'children' not in obj:
            return
        obj['children'] = [objs[i] for i in obj['children']]
        for children_obj in obj['children']:
            _set_children_objs(children_obj)

    for root in roots:
        _set_children_objs(root)

    return roots

def describe_single_rectangular(rect: dict) -> dict:
    obj = rect['obj']
    if not obj:
        raise ValueError('Cannot describe empty rectangle') 
    w, h = rect['w'], rect['h']
    if w == 1 or h == 1:            
        result = describe_single_line(rect['obj'])
    else:
        result = dict(shape='rectangle', topleft_yx=(rect['tl_y'], rect['tl_x']), height=h, width=w)
        if rect['thickness'] != 0:
            result['thickness'] = rect['thickness']
    
    result.update(get_color_dict(obj)) 
    if result['shape'] not in ['point', 'line']:
        result['has_hole'] = has_hole(obj) # add has_hole at the end, to be consistent with elsewhere
    return result


def describe_single_irregular(obj: Object, rectangles: list[dict], irregular_method: Literal['raw','rectangles','vlines', 'hlines']) -> dict:
    # if isinstance(obj, dict):
    #     obj = obj['obj']
    result = dict(shape='irregular', size=len(obj), bounding_box=bounding_box_(obj))
    result.update(get_color_dict(obj))
    result['has_hole'] = has_hole(obj) # add has_hole at the end, to be consistent with elsewhere
    if irregular_method == 'raw':
        pass
    elif irregular_method == 'rectangles':
        result['as_rectangles'] = []
        for rectangle in rectangles:
            result['as_rectangles'].append(describe_single_rectangular(rectangle))
    elif irregular_method in ['vlines','hlines']:
        result[f'as_{irregular_method}'] = describe_single_object_as_one_or_more_lines(obj, direction='vertical' if irregular_method=='vlines' else 'horizontal')
    return result

def get_color_dict(obj: Object) -> dict:
    if isinstance(obj, dict):
        obj = obj['obj']
    obj_colors = [col for _, col in obj]
    colors = list(set(color_to_str_dict_[col] for col in set(obj_colors)))
    colors_str = ','.join(colors)
    color_key = 'color' if len(colors) == 1 else 'colors'
    return {color_key: colors_str}

def describe_single_object_as_one_or_more_rectangulars(obj: Object, irregular_method: Literal['raw','rectangles','vlines', 'hlines']='raw') -> dict:
    """ one or more rectangluars are saved in an irregular object's `as_X` key where X is `irregular_method` """
    # if isinstance(obj, dict):
    #     obj = obj['obj']
    def describe_single_object_as_one_or_more_rectangulars_(obj: Object) -> list[dict]:
        results = []
        positions = set(pos for pos, _ in obj)
        while positions:
            rect = find_rectangle_in_positions_(positions)        
            if rect is None:
                break
            else:
                rect_positions = set(rect['positions'])            
                rect['obj'] = get_subobject(obj, rect_positions)
                results.append(rect)
                positions -= rect_positions
        
        return results
    
    if not obj:
        raise ValueError('Cannot describe empty object.')
    assert irregular_method in ['raw', 'rectangles', 'vlines', 'hlines']
    
    obj_positions = [pos for pos, _ in obj]
    rectangles = describe_single_object_as_one_or_more_rectangulars_(obj)
    if len(rectangles) == 1 and set(obj_positions) == set(rectangles[0]['positions']):
        result = describe_single_rectangular(rectangles[0])
    else:
        result = describe_single_irregular(obj, rectangles, irregular_method)
                    
    return result

@ignore_for_llm_tools_docs
def get_rectangles_ordered_by_area_(W, H):
    result = []
    for w in range(1, W+1):
        for h in range(1, H+1):
            result.append((w,h))
    return sorted(result, key=lambda e: e[0]*e[1], reverse=True)

# set for speedup
def find_rectangle_in_positions_(positions: set) -> dict:
    xs = [x for y, x in positions]
    ys = [y for y, x in positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    W, H = max_x - min_x + 1, max_y - min_y + 1

    filled_positions = set(get_rectangle_positions_(min_y, min_x, W, H, t=0))
    if positions == filled_positions:
        return dict(shape='rectangle', positions=list(filled_positions), w=W, h=H, tl_x=min_x, tl_y=min_y, thickness=0)
    
    # prioritize w+h, so a 4x4 rectangle is found before a 17x1 line
    for w, h in get_rectangles_ordered_by_area_(W,H):
        max_border_thickness = max(1, min(w, h) // 2)
        max_tl_x = max_x - w + 1
        max_tl_y = max_y - h + 1
        for tl_x in range(min_x, max_tl_x + 1):
            for tl_y in range(min_y, max_tl_y + 1):                 
                for thickness in range(max_border_thickness,0,-1): # t=0 (filled) is not included here and handled above
                    rect_positions_array = get_rectangle_positions_(tl_y, tl_x, w, h, thickness)
                    rect_positions = set(rect_positions_array)
                    # rect_positions = set(map(tuple, rect_positions_array))
                    if rect_positions <= positions:
                        return dict(shape='rectangle', positions=list(rect_positions), w=w, h=h, tl_x=tl_x, tl_y=tl_y, thickness=thickness)
    return None


get_rectangle_positions_cache_ = dict()
def get_rectangle_positions_(tl_y, tl_x, w, h, t):
    if (w,h,t) not in get_rectangle_positions_cache_:
        get_rectangle_positions_cache_[(w,h,t)] = get_rectangle_positions_do_(0, 0, w, h, t)
    
    rect_0_0 = get_rectangle_positions_cache_[(w,h,t)]
    # rect_0_0_np = np.array(rect_0_0)
    # offsets = np.array([tl_y, tl_x])
    # result = rect_0_0_np + offsets
    # return result

    return [(y+tl_y, x+tl_x) for y,x in rect_0_0]
    
@ignore_for_llm_tools_docs
def get_rectangle_positions_do_(tl_y, tl_x, w, h, t):
    """ t is thickness, t=0 gives a solid (filled) rectangle. """
    max_border_thickness = max(1, min(h, w) // 2)
    if t < 0 or t > max_border_thickness:
        raise ValueError(
            f"`t` shoudl be non-negative number less than or equal `{max_border_thickness=}` (for `{h=}` and `{w=}`), but got `{t=}`"
        )
    
    positions = []
    if t == 0:
        # Fill the rectangle completely
        for y in range(tl_y, tl_y + h):
            for x in range(tl_x, tl_x + w):
                positions.append((y, x))
    elif t == 1:
        # Include only the perimeter (outline) of the rectangle
        for y in range(tl_y, tl_y + h):
            for x in range(tl_x, tl_x + w):
                if y == tl_y or y == tl_y + h - 1 or x == tl_x or x == tl_x + w - 1:
                    positions.append((y, x))
    else:
        # Include the border of thickness t
        for y in range(tl_y, tl_y + h):
            for x in range(tl_x, tl_x + w):
                if (y - tl_y < t or (tl_y + h - 1 - y) < t or
                    x - tl_x < t or (tl_x + w - 1 - x) < t):
                    positions.append((y, x))
    return positions

############################
# Top level grid lenses: (2) as lines (vertical/horizontal)
def parse_grid_as_lines(grid: Grid, direction: str, bg_color: int=0) -> list[dict]:
    assert direction in ['horizontal', 'vertical']
    # def get_grid_as_obj(grid: Grid) -> Object:
    #     return [((y,x),grid[y][x]) for y in range(len(grid)) for x in range(len(grid[0]))]

    H, W = len(grid), len(grid[0])
    if direction == 'horizontal':        
        lines = [{'obj': [((y,x),grid[y][x]) for x in range(W) if grid[y][x] != bg_color]} for y in range(H)]
    else:
        lines = [{'obj': [((y,x),grid[y][x]) for y in range(H) if grid[y][x] != bg_color]} for x in range(W)]

    results = []
    for line in lines:
        if line:
            line.update(describe_single_line(line['obj']))
            results.append(line)
    return results


def describe_single_object_as_one_or_more_lines(obj: Object, direction: Literal['vertical', 'horizontal']):
    # if isinstance(obj, dict):
    #     obj = obj['obj']
    obj_positions = dict.fromkeys(pos for pos, _  in obj)
    xs = [x for y, x in obj_positions]
    ys = [y for y, x in obj_positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    W, H = max_x - min_x + 1, max_y - min_y + 1
    
    if direction == 'horizontal':        
        lines = [{'obj': [((y,x),grid[y][x]) for x in range(W) if grid[y][x] != bg_color]} for y in range(H)]
    else:
        lines = [{'obj': [((y,x),grid[y][x]) for y in range(H) if grid[y][x] != bg_color]} for x in range(W)]

    # grid = [[(1 if (y+min_y,x+min_x) in obj_positions else 0) for y in range(h)] for x in range(w)]
    # return parse_grid_as_lines(grid, direction, bg_color=0)


def describe_single_line(obj: Object) -> dict:
    # if isinstance(obj, dict):
    #     obj = obj['obj']
    if not obj:
        raise ValueError('Cannot describe mepty object.')
    obj_positions = [pos for pos, _  in obj]
    xs = [x for y, x in obj_positions]
    ys = [y for y, x in obj_positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    w, h = max_x - min_x + 1, max_y - min_y + 1
    first_pos = obj_positions[0]
    if (w,h) == (1,1):            
        result = dict(shape='point', position=first_pos)
    elif w == 1:
        result = dict(shape='line', direction='vertical', x=first_pos[0], start_y=min_y, end_y=max_y, length=len(obj))
    elif h == 1:
        result = dict(shape='line', direction='horizontal', y=first_pos[1], start_x=min_x, end_x=max_x, length=len(obj))

    result.update(get_color_dict(obj))
    return result

# def get_object_as_lines_topological(obj: Object, direction: str) -> list[dict]:
#     """
#     Decompose a univalued object into contiguous lines based on the specified direction.

#     Parameters:
#     - obj (Object): An iterable of tuples, each containing a position (y, x) and a color.
#                     Example: [((0, 0), 'blue'), ((0, 1), 'blue'), ...]
#     - direction (str): The direction to extract lines. Must be either 'horizontal' or 'vertical'.
#                        - 'horizontal': Lines are sequences of contiguous points along the same row (constant y).
#                        - 'vertical': Lines are sequences of contiguous points along the same column (constant x).

#     Returns:
#     - List[Indices]: A list where each element is a list of contiguous (y, x) positions representing a line.

#     Raises:
#     - ValueError: If the direction is not 'horizontal' or 'vertical'.
#     - TypeError: If the input types are incorrect.
#     """
#     if direction not in ('horizontal', 'vertical'):
#         raise ValueError("direction must be either 'horizontal' or 'vertical'")

#     obj_positions = set(pos for pos, _ in obj)
#     groups = defaultdict(list)  # key: grouping key, value: list of positions

#     if direction == 'horizontal':
#         for y, x in obj_positions:
#             groups[y].append(x)
#     else:
#         for y, x in obj_positions:
#             groups[x].append(y)

#     lines_positions = []

#     # Process each group to find contiguous sequences
#     for key in sorted(groups):
#         if direction == 'horizontal':
#             # Sort x positions within the row
#             sorted_coords = sorted(groups[key])
#             current_line = []
#             prev = None
#             for x in sorted_coords:
#                 if prev is None or x == prev + 1:
#                     current_line.append((key, x))
#                 else:
#                     if current_line:
#                         lines_positions.append(current_line)
#                     current_line = [(key, x)]
#                 prev = x
#             if current_line:
#                 lines_positions.append(current_line)
#         else:
#             # 'vertical' direction: sort y positions within the column
#             sorted_coords = sorted(groups[key])
#             current_line = []
#             prev = None
#             for y in sorted_coords:
#                 if prev is None or y == prev + 1:
#                     current_line.append((y, key))
#                 else:
#                     if current_line:
#                         lines_positions.append(current_line)
#                     current_line = [(y, key)]
#                 prev = y
#             if current_line:
#                 lines_positions.append(current_line)

#     results = []
#     for line_positions in lines_positions:
#         results.append(dict(shape='line', positions=line_positions, obj=get_subobject(obj, line_positions)))

#     return results
    

############################
# Actions
@llm_tool
def put_obj_on_grid(grid: Grid, obj: Object, clip: bool=True) -> None:
    """ Put `object` on `grid`. If `clip=False`, then the grid must have enough space for the object's coordinates. """
    if isinstance(obj, dict):
        obj = obj['obj']
    tl_y, tl_x = 0, 0
    gh, gw = len(grid), len(grid[0])
    for (y,x), col in obj:
        if not clip or (y+tl_y < gh and x+tl_x < gw): # if clip is False, we try to set grid anyway
            grid[y+tl_y][x+tl_x] = col
    
    
@llm_tool
def move_object(obj: Object, tl_yx: tuple[int, int]=(0, 0)) -> Object:
    """ Move `object` so that topleft yx-coordinate of the object's bounding box coincides with `tl_xy`. """
    if isinstance(obj, dict):
        obj = obj['obj']
    tl_y, tl_x = tl_yx
    positions = set(pos for pos, _ in obj)
    xs = [x for y, x in positions]
    ys = [y for y, x in positions]
    min_x, min_y  = min(xs), min(ys)
    new_obj = [((y-min_y+tl_y, x-min_x+tl_x), col) for (y,x),col in obj]
    return new_obj

def rotate_object(obj: Object, angle: int):
    ...

# @llm_tool
# def filter_objects_by_color(objs: list[Object], color: int):
#     return [obj for obj in objs if get_obj_colors(obj) == {color}]

# @llm_tool
# def filter_objects_by_size(objs: list[Object], size: int):
#     return [obj for obj in objs if len(obj) == size]