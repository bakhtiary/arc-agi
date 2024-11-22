from tools_src_mini import (Object, get_num_colors, get_object_as_rectangles_and_lines_topological, 
    describe_rectangle_or_line_or_point_univalued,
    color_to_str_dict_, has_hole, obj_to_univalued)

def bounding_box_(obj: Object) -> tuple[tuple[int,int],tuple[int,int]]:
    """ Returns ((tl_y,tl_x),(br_y,br_x)) where t/b is for top/bottom and r/l for right/left """
    positions = set(pos for pos, _ in obj)
    xs = [x for y, x in positions]
    ys = [y for y, x in positions]
    min_x, max_x, min_y, max_y  = min(xs), max(xs), min(ys), max(ys)
    return ((min_y, min_x), (max_y, max_x))


def dict_to_str(d: dict) -> str:
    return f'({", ".join(f"{key}={value}" for key, value in d.items())})'

def desc_to_nested_str(d: dict, indent=0) -> str:
    result = ''
    children = []
    if 'children' in d:
        children = d['children']
        del d['children']
    result += '\t' * indent + dict_to_str(d)
    for child in children:
        result += '\n' + desc_to_nested_str(child, indent+1)        
    return result

# @llm_lense_tool
# @llm_tool
def describe_objects_orthogonal_flat(objs: list[Object], univalued: bool) -> list[dict]:
    descs = []
    if univalued:
        for obj in objs:
            if get_num_colors(obj) != 1:
                raise ValueError(f'Object `{obj}` not univalued, but `{univalued=}`.')
            descs.append(describe_object_orthogonal_univalued(obj))
    else:
        for obj in objs:
            descs.append(describe_object_orthogonal_colored(obj))
    
    return descs


def describe_objects_orthogonal_hierarchy(objs: list[dict], univalued: bool) -> list[dict]:
    if not objs:
        return [] 
    if not isinstance(objs[0], dict):
        raise ValueError('`objs` should be a list of dicts with an `obj: Object` key.')
    
    def describe_obj_(obj: dict):
        if univalued:
            if get_num_colors(obj['obj']) != 1:
                raise ValueError(f'Object `{obj}` not univalued, but `{univalued=}`.')
            result = describe_object_orthogonal_univalued(obj['obj'])
        else:
            result = describe_object_orthogonal_colored(obj['obj'])

        children = []
        if 'children' in obj:
            for child_obj in obj['children']:
                children.append(describe_obj_(child_obj))
            result['children'] = children            
        return result
    descs = []
    for obj in objs:
        descs.append(describe_obj_(obj))
    
    return descs


# @llm_lense_tool
def describe_object_orthogonal_univalued(obj: Object) -> dict:
    if not obj:
        raise ValueError('Cannot describe empty object.')
    obj_positions = [pos for pos, _ in obj]
    _, color = obj[0]
    rectangles = get_object_as_rectangles_and_lines_topological(obj)
    if len(rectangles) == 1 and set(obj_positions) == set(rectangles[0]['positions']):
        result = describe_rectangle_or_line_or_point_univalued(rectangles[0])
        result.update(color=color_to_str_dict_[color])
        if result['shape'] not in ['point', 'line']:
            result['has_hole']=has_hole(obj)
    # elif : tilted lines
    # elif: traingles ...
    # elif: L-shapes ...
    else:
        result = dict(shape='irregular', size=len(obj), bounding_box=bounding_box_(obj),
            color=color_to_str_dict_[color], has_hole=has_hole(obj))
        
        # result.update(as_rectangles=[], as_horizontal_lines=[], as_vertical_lines=[])
        
        # for rectangle in rectangles:
        #     result['as_rectangles'].append(describe_rectangle_or_line_or_point_univalued(rectangle))
        
        # horizontal_lines = get_object_as_lines_topological(obj, direction='horizontal')
        # for line in horizontal_lines:
        #     result['as_horizontal_lines'].append(describe_line_univalued(line))

        # vertical_lines = get_object_as_lines_topological(obj, direction='vertical')
        # for line in vertical_lines:
        #     result['as_vertical_lines'].append(describe_line_univalued(line))
    
    return result


def describe_object_orthogonal_colored(obj: Object) -> dict:
    if not obj:
        raise ValueError('Cannot describe empty object')
    obj_positions = [pos for pos, _ in obj]
    obj_colors = [col for _, col in obj]
    colors = list(set(color_to_str_dict_[col] for col in set(obj_colors)))
    colors_str = '"' + ','.join(colors) + '"'
    unicolored_obj = obj_to_univalued(obj)
    rectangles = get_object_as_rectangles_and_lines_topological(unicolored_obj)
    if len(rectangles) == 1 and set(obj_positions) == set(rectangles[0]['positions']):
        result = describe_rectangle_or_line_or_point_univalued(rectangles[0])
        if len(colors) == 1:
            result['color'] = colors[0]
        else:
            result['colors'] = colors_str
        if result['shape'] not in ['point', 'line']:
            result['has_hole'] = has_hole(obj)
    # elif : tilted lines
    # elif: traingles ...
    # elif: L-shapes ...
    else:
        result = dict(shape='irregular', size=len(obj), bounding_box=bounding_box_(obj))
        if len(colors) == 1:
            result.update(color=colors[0], has_hole=has_hole(obj)) # add has_hole at the end, to be consistent with elsewhere
        else:
            result.update(color=colors_str, has_hole=has_hole(obj)) # add has_hole at the end, to be consistent with elsewhere
        
        # result.update(as_rectangles=[], as_horizontal_lines=[], as_vertical_lines=[])
        
        # for rectangle in rectangles:
        #     result['as_rectangles'].append(describe_rectangle_or_line_or_point_colored(rectangle))
        
        # horizontal_lines = get_object_as_lines_topological(obj, direction='horizontal')
        # for line in horizontal_lines:
        #     result['as_horizontal_lines'].append(describe_line_colored(line))

        # vertical_lines = get_object_as_lines_topological(obj, direction='vertical')
        # for line in vertical_lines:
        #     result['as_vertical_lines'].append(describe_line_colored(line))
    
    return result
