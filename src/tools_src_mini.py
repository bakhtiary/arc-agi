## flood fill, connect lines, describe shapes (with discribe inside, but about unconnected shapes with an "invisible" tie, or
# black squares on a large yellow rectangle)
from collections import defaultdict
import functools

import numpy as np
from code_utils import ignore_for_llm_tools_docs, llm_action_tool, llm_lense_tool, llm_tool
from collections import deque

Grid = list[list[int]]
Object = list[tuple[tuple[int,int], int]]
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

def obj_func_cacher(func):
    cache_ = dict()
    def _wrapper(obj: Object):
        obj_as_set = frozenset(obj)
        if obj_as_set not in cache_:
            cache_[obj_as_set] = func(obj)
        return cache_[obj_as_set]
    return _wrapper


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

@llm_tool
def most_common_color(element: Object|Grid) -> int:
    """ most common color in an object or a grid """
    if isinstance(element[0], tuple): # an object
        values = [x[1] for x in element]
    else:
        values = [cell for row in element for cell in row]
    return max(set(values), key=values.count)

@llm_tool
def get_num_colors(element: Object|Grid) -> int:
    """ number of colors in an object or a grid """
    if isinstance(element[0], tuple): # an object
        values = [x[1] for x in element]
    else:
        values = [cell for row in element for cell in row]
    return len(set(values))


def has_hole(obj: Object):
    """ Determine if the object has a hole."""
    # return len(get_hole_points(obj)) != 0
    min_y, min_x, w, h, grid, visited = get_grid_and_visited_for_hole_functions_(obj)
    for y in range(h):
        for x in range(w):
            if grid[y][x] == 0 and not visited[y][x]:
                return True  # Hole detected

    return False

@llm_action_tool
def flood_fill(obj: Object, color: int):
    return obj + [(pos, color) for pos in get_hole_positions(obj)]

@llm_tool
def get_hole_positions(obj: Object) -> Indices:
    min_y, min_x, w, h, grid, visited = get_grid_and_visited_for_hole_functions_(obj)
    return list((min_y + y, min_x + x) for y in range(h) for x in range(w) if grid[y][x] == 0 and not visited[y][x])

# @llm_tool
def get_filled_positions(obj: Object) -> Indices:
    return list(pos for pos, _ in obj) + get_hole_positions(obj)
          
@ignore_for_llm_tools_docs
@obj_func_cacher
def get_grid_and_visited_for_hole_functions_(obj):
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

@ignore_for_llm_tools_docs
def get_rectangles_ordered_by_area_(W, H):
    result = []
    for w in range(1, W+1):
        for h in range(1, H+1):
            result.append((w,h))
    return sorted(result, key=lambda e: e[0]*e[1], reverse=True)


def obj_to_univalued(obj: Object, uni_color=0):
   return [(pos, uni_color) for pos, _ in obj]

def get_subobject(obj: Object, positions: dict):
    positions = dict.fromkeys(positions)
    return [(x,c) for x,c in obj if x in positions]

get_rectangle_positions_cache_ = dict()
def get_rectangle_positions_(bl_y, bl_x, w, h, t):
    if (w,h,t) not in get_rectangle_positions_cache_:
        get_rectangle_positions_cache_[(w,h,t)] = get_rectangle_positions_do_(0, 0, w, h, t)
    
    rect_0_0 = get_rectangle_positions_cache_[(w,h,t)]
    # rect_0_0_np = np.array(rect_0_0)
    # offsets = np.array([bl_y, bl_x])
    # result = rect_0_0_np + offsets
    # return result

    return [(y+bl_y, x+bl_x) for y,x in rect_0_0]
    
@ignore_for_llm_tools_docs
def get_rectangle_positions_do_(bl_y, bl_x, w, h, t):
    """ t is thickness, t=0 gives a solid (filled) rectangle. """
    max_border_thickness = max(1, min(h, w) // 2)
    if t < 0 or t > max_border_thickness:
        raise ValueError(
            f"`t` shoudl be non-negative number less than or equal `{max_border_thickness=}` (for `{h=}` and `{w=}`), but got `{t=}`"
        )
    
    positions = []
    if t == 0:
        # Fill the rectangle completely
        for y in range(bl_y, bl_y + h):
            for x in range(bl_x, bl_x + w):
                positions.append((y, x))
    elif t == 1:
        # Include only the perimeter (outline) of the rectangle
        for y in range(bl_y, bl_y + h):
            for x in range(bl_x, bl_x + w):
                if y == bl_y or y == bl_y + h - 1 or x == bl_x or x == bl_x + w - 1:
                    positions.append((y, x))
    else:
        # Include the border of thickness t
        for y in range(bl_y, bl_y + h):
            for x in range(bl_x, bl_x + w):
                if (y - bl_y < t or (bl_y + h - 1 - y) < t or
                    x - bl_x < t or (bl_x + w - 1 - x) < t):
                    positions.append((y, x))
    return positions

@llm_tool
def get_grid_objects_as_flat_list(grid: Grid, univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None) -> list[Object]:
    """ Extract connected objects from a grid.

    Args:
        grid (List[List[int]]): A 2D grid represented as a list of lists of integers.
        univalued (bool): If True, only consider connected cells with the same value as part of an object.
                          If False, any non-background value is included in the object.
        diagonal (bool): If True, include diagonal neighbors when determining connectivity.
                         If False, only consider orthogonal neighbors (up, down, left, right).
        with_bg (bool): If True, considers the background value, when finding objects and background cells might be part of the objects returned.
            (Note: when univalued is True, with_bg leads to include univalued background patches)
        bg_color (int, optional): Specifies the background color in the grid to be used with `with_bg`=False.

    Returns:
        List[Object]: A list of objects, where each object is a list of tuples like ((row index, column index), value).
    
    Note:
        univalued=True, with_bg=True --> all univalued objects, including background patches (so, bg_color is not needed)
        univalued=True, with_bg=False -->  all univalued objects other than background patches
        univalued=False, with_bg=True -->  the grid as a single object (so, bg_color is not needed)
        univalued=False, with_bg=False -->  all colored objects seperated by background

    Note 2:
        Please specify `bg_color` with `with_bg=False`
    """
   
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



def describe_rectangle_or_line_or_point_univalued(rectangle: dict) -> dict:
    rectangle_positions = rectangle['positions']
    if not rectangle_positions:
        raise ValueError('Cannot describe empty rectangle')
    w, h = rectangle['w'], rectangle['h']
    first_pos = rectangle_positions[0]
    if (w,h) == (1,1):            
        return dict(shape='point', position=first_pos)
    elif w == 1:
        return dict(shape='line', direction='vertical', x=first_pos[0], length=len(rectangle_positions))
    elif h == 1:
        return dict(shape='line', direction='horizontal', y=first_pos[1], length=len(rectangle_positions))
    else:
        result = dict(shape='rectangle', buttomleft=(rectangle['tl_x'],rectangle['tl_y']), width=w, height=h)
        if rectangle['thickness'] != 0:
            result['thickness'] = rectangle['thickness']
        return result

def describe_line_univalued(line: dict) -> dict:
    line_positions = line['positions']
    if not line_positions:
        raise ValueError('Cannot describe empty line')
    xs = [x for y, x in line_positions]
    ys = [y for y, x in line_positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    w, h = max_x - min_x + 1, max_y - min_y + 1
    first_pos = line_positions[0]
    if (w,h) == (1,1):            
        return dict(shape='point', position=first_pos)
    elif w == 1:
        return dict(shape='line', direction='vertical', x=first_pos[0], length=len(line_positions))
    elif h == 1:
        return dict(shape='line', direction='horizontal', y=first_pos[1], length=len(line_positions))

def describe_line_colored(line: dict) -> dict:
    result = describe_line_univalued(line)
    result['num_colors'] = get_num_colors(line['obj']) 
    return result

def get_object_as_lines_topological(obj: Object, direction: str) -> list[dict]:
    """
    Decompose a univalued object into contiguous lines based on the specified direction.

    Parameters:
    - obj (Object): An iterable of tuples, each containing a position (y, x) and a color.
                    Example: [((0, 0), 'blue'), ((0, 1), 'blue'), ...]
    - direction (str): The direction to extract lines. Must be either 'horizontal' or 'vertical'.
                       - 'horizontal': Lines are sequences of contiguous points along the same row (constant y).
                       - 'vertical': Lines are sequences of contiguous points along the same column (constant x).

    Returns:
    - List[Indices]: A list where each element is a list of contiguous (y, x) positions representing a line.

    Raises:
    - ValueError: If the direction is not 'horizontal' or 'vertical'.
    - TypeError: If the input types are incorrect.
    """
    if direction not in ('horizontal', 'vertical'):
        raise ValueError("direction must be either 'horizontal' or 'vertical'")

    obj_positions = set(pos for pos, _ in obj)
    groups = defaultdict(list)  # key: grouping key, value: list of positions

    if direction == 'horizontal':
        for y, x in obj_positions:
            groups[y].append(x)
    else:
        for y, x in obj_positions:
            groups[x].append(y)

    lines_positions = []

    # Process each group to find contiguous sequences
    for key in sorted(groups):
        if direction == 'horizontal':
            # Sort x positions within the row
            sorted_coords = sorted(groups[key])
            current_line = []
            prev = None
            for x in sorted_coords:
                if prev is None or x == prev + 1:
                    current_line.append((key, x))
                else:
                    if current_line:
                        lines_positions.append(current_line)
                    current_line = [(key, x)]
                prev = x
            if current_line:
                lines_positions.append(current_line)
        else:
            # 'vertical' direction: sort y positions within the column
            sorted_coords = sorted(groups[key])
            current_line = []
            prev = None
            for y in sorted_coords:
                if prev is None or y == prev + 1:
                    current_line.append((y, key))
                else:
                    if current_line:
                        lines_positions.append(current_line)
                    current_line = [(y, key)]
                prev = y
            if current_line:
                lines_positions.append(current_line)

    results = []
    for line_positions in lines_positions:
        results.append(dict(shape='line', positions=line_positions, obj=get_subobject(obj, line_positions)))

    return results
    


def get_object_as_rectangles_and_lines_topological(obj: Object) -> list[dict]:
    """ Example: for a blue square filled with black, if object is returned by get_grid_objects with univalued=True, then object contains holes (topogically), but does not contain black cells.
    Object is not required to be univalued, but by considering only the position information and not the colors, it is virtually treated as such.
    """ 
    # TODO: find rectangles (inclduing zones?, i.e., with boundaries as borders --> describe blacks as well)
    def _find_rectangle_in_positions(positions):        
        xs = [x for y, x in positions]
        ys = [y for y, x in positions]
        min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
        W, H = max_x - min_x + 1, max_y - min_y + 1
        
        # prioritize w+h, so a 4x4 rectangle is found before a 17x1 line
        for w, h in get_rectangles_ordered_by_area_(W,H):
            max_border_thickness = max(1, min(w, h) // 2)
            max_tl_x = max_x - w + 1
            max_tl_y = max_y - h + 1
            for tl_x in range(min_x, max_tl_x + 1):
                for tl_y in range(min_y, max_tl_y + 1):                 
                    for thickness in range(max_border_thickness,-1,-1): # 0 for points and lines (0D/1D objects)
                        rect_positions_array = get_rectangle_positions_(tl_y, tl_x, w, h, thickness)
                        rect_positions = set(rect_positions_array)
                        # rect_positions = set(map(tuple, rect_positions_array))
                        if rect_positions <= positions:
                            return dict(shape='rectangle', positions=list(rect_positions), w=w, h=h, tl_x=tl_x, tl_y=tl_y, thickness=thickness)
        return None
    
    results = []
    positions = set(pos for pos, _ in obj)
    while positions:
        rect = _find_rectangle_in_positions(positions)        
        if rect is None:
            break
        else:
            rect_positions = set(rect['positions'])            
            rect['obj'] = get_subobject(obj, rect_positions)
            results.append(rect)
            positions -= rect_positions
    
    return results

####
# @llm_tool
def get_grid_objects_hierarchy(grid: Grid, univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None) -> list[dict]:
    """ Extract connected objects from a grid. The return value is a list of root objects with keys `obj: Object` and `children: list[dict]`

    Args:
        grid (List[List[int]]): A 2D grid represented as a list of lists of integers.
        univalued (bool): If True, only consider connected cells with the same value as part of an object.
                          If False, any non-background value is included in the object.
        diagonal (bool): If True, include diagonal neighbors when determining connectivity.
                         If False, only consider orthogonal neighbors (up, down, left, right).
        with_bg (bool): If True, considers the background value, when finding objects and background cells might be part of the objects returned.
            (Note: when univalued is True, with_bg leads to include univalued background patches)
        bg_color (int, optional): Specifies the background color in the grid to be used with `with_bg`=False.

    Returns:
        List[Object]: A list of objects, where each object is a list of tuples like ((row index, column index), value).
    
    Note:
        univalued=True, with_bg=True --> all univalued objects, including background patches (so, bg_color is not needed)
        univalued=True, with_bg=False -->  all univalued objects other than background patches
        univalued=False, with_bg=True -->  the grid as a single object (so, bg_color is not needed)
        univalued=False, with_bg=False -->  all colored objects seperated by background

    Note 2:
        Please specify `bg_color` with `with_bg=False`
    """

    if not with_bg and bg_color is None:
        raise ValueError('Please specify `bg_color` with `with_bg=False`.')
   
    objs = get_grid_objects_as_flat_list(grid, univalued, diagonal, with_bg, bg_color)
    
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