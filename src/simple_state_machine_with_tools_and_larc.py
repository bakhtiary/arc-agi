from datetime import datetime
import json
from pathlib import Path
import re
import pandas as pd
from code_utils import generate_tools_docs_by_ast
from dataset import Dataset
from grid_utils import get_grid_sizes, AKGrid
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from llm_utils import LLMInterface
from state_machine_solver_utils import extract_and_run_mapping_code
from tools_src_mini import BLACK, BROWN, color_to_str, make_grid_monochrome, parse_grid_as_lines, parse_grid_as_objects, parsed_single_thing_to_str, parsed_things_to_str, parsed_things_to_str_json, str_to_color

current_file_dir = Path(__file__).parent

class SimpleStateMachineWithToolsAndLarc:
    """
        workflow: entry_point
            --> ask_for_code (`solve`, hardcoded tools)
    """
    def __init__(self, task_id, dataset: Dataset, distinct_pairs=True, which_pairs: str|list[int]='all'):
        self.start_state = 'entry_point'
        self.phase = 'all_in_one'
        self.states = {}
        self.dataset = dataset
        self.run_results: list[list[dict]] = [] # each run result is a list of dicts such as [{'text': xx}, {'grid': [[1]]}, ...]
        self.task_id = task_id
        self.task = dataset.read_task(task_id)
        self.solution: list[AKGrid] = None # one solution for each test case
        self.max_num_failed = 7
        self.num_failed = 0
        self.distinct_pairs = distinct_pairs
        self.which_pairs = which_pairs
        self.tools: list[dict]  = None # each tool is a dict {'name': 'f', 'signature': 'def f ...', 'code': 'import xx;\n...'}
        self.hypothesis = None
        self.default_input_grid_lens = None
        self.default_output_grid_lens = None
        self.default_input_grid_lens_code = None
        self.default_output_grid_lens_code = None
        self.default_co_grid_lens = None # TODO
        self.monochromatic_useful = None
        self.monochromatic_bg = None

        if task_id == 'b2862040':
            self.bg_color = BROWN
        else:
            self.bg_color = BLACK


        self.descriptors = [
            # objects/orthogonal
            dict (
                id='objects/orthogonal,with-bg/rectangulars/irregular:raw',
                desc='A set of uivalued objects (orthogonally connected) described as rectangulars',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=False, with_bg=True, object_describer='rectangulars/irregular:raw'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=False, with_bg=True, hierarchical=True, object_describer="rectangulars/irregular:raw")'
            ),
            dict(
                id='objects/orthogonal,with-bg/rectangulars/irregular:rectangulars',
                desc='A set of  univalued objects (orthogonally connected) described as rectangulars (+ irregulars as rectangulars)',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=False, with_bg=True, object_describer='rectangulars/irregular:rectangulars'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=False, with_bg=True, hierarchical=True, object_describer="rectangulars/irregular:rectangulars")',
            ),
            dict (
                id='objects/orthogonal,without-bg/rectangulars/irregular:raw',
                desc='A set of uivalued objects (orthogonally connected) described as rectangulars',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=False, with_bg=False, object_describer='rectangulars/irregular:raw'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=False, with_bg=False, bg_color={self.bg_color}, hierarchical=True, object_describer="rectangulars/irregular:raw")',
            ),
            dict(
                id='objects/orthogonal,without-bg/rectangulars/irregular:rectangulars',
                desc='A set of  univalued objects (orthogonally connected) described as rectangulars (+ irregulars as rectangulars)',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=False, with_bg=False, object_describer='rectangulars/irregular:rectangulars'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=False, with_bg=False, bg_color={self.bg_color}, hierarchical=True, object_describer="rectangulars/irregular:rectangulars")',
            ),
            # dict (
            #     desc='A set of univalued objects (orthogonally connected) described as rectangulars (+ irregulars as vertical lines)',
            #     func=...
            # ),
            # dict(
            #     desc='A set of univalued objects (orthogonally connected) described as rectangulars (+ irregulars as horizontal lines)'
            # ),

            # objects / diagonal
            dict (
                id='objects/diagonal,with-bg/rectangulars/irregular:raw',
                desc='A set of uivalued objects (diagonally connected) described as rectangulars',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=True, with_bg=True, object_describer='rectangulars/irregular:raw'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=True, with_bg=True, hierarchical=True, object_describer="rectangulars/irregular:raw")'

            ),
            dict(
                id='objects/diagonal,with-bg/rectangulars/irregular:rectangulars',
                desc='A set of  univalued objects (diagonally connected) described as rectangulars (+ irregulars as rectangulars)',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=True, with_bg=True, object_describer='rectangulars/irregular:rectangulars'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=True, with_bg=True, hierarchical=True, object_describer="rectangulars/irregular:rectangulars")',
            ),
             dict (
                id='objects/diagonal,without-bg/rectangulars/irregular:raw',
                desc='A set of uivalued objects (diagonally connected) described as rectangulars',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=True, with_bg=False, object_describer='rectangulars/irregular:raw'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=True, with_bg=False, bg_color={self.bg_color}, hierarchical=True, object_describer="rectangulars/irregular:raw")',

            ),
            dict(
                id='objects/diagonal,without-bg/rectangulars/irregular:rectangulars',
                desc='A set of  univalued objects (diagonally connected) described as rectangulars (+ irregulars as rectangulars)',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='objects', diagonal=True, with_bg=False, object_describer='rectangulars/irregular:rectangulars'),
                code='parse_grid_as_objects(grid, univalued=True, diagonal=True, with_bg=False, bg_color={self.bg_color}, hierarchical=True, object_describer="rectangulars/irregular:rectangulars")',
            ),
            # dict (
            #     desc='A set of univalued objects (diagonally connected) described as rectangulars (+ irregulars as vertical lines)',
            #     func=...
            # ),
            # dict(
            #     desc='A set of univalued objects (diagonally connected) described as rectangulars (+ irregulars as horizontal lines)'
            # ),

            ## lines
            dict(
                id='vlines',
                desc='A set of vertical lines',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='vlines'),
                code='parse_grid_as_lines(grid, "vertical")'
            ),
            dict(
                id='hlines',
                desc='A set of horizontal lines',
                func=lambda grid: self.grid_to_lens_str_json(grid, parse_type='hlines'),
                code='parse_grid_as_lines(grid, "horizontal")'
            )
        ]
        

        self.states['entry_point'] = dict(
            message_to_send=[
                lambda: f'''The final goal of this conversation is to that you write a Python function that successfully maps the input grids to the output grids.
Here is a description of the grids: {self.send_larc_description()}

We're going to do this in multiple rounds where you have the chance to write Python codes and recieve the results.

Related types and constants:
```
Grid = list[list[int]]
Object = list[tuple[tuple[int,int], int]] # used in object's `obj` key as described below. It's a list of ((y,x),color) tuples
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
```

In each turn you write a code containing a function `solve(grid: Grid) -> Grid`, that implements your proposed mapping. I will execute the function on all input grids and tell you the results.
To help you, I have  written a basic set of tools that you might find useful:
- `parse_grid_as_objects (grid: Grid, univalued: bool, diagonal: bool, with_bg: bool=True, bg_color: int=None, hierarchical: bool=True) -> list[dict]`.
Depending on the arguments, the function returns a list of objects, i.e., a set of either univalued or multi-valued-non-background, othogonally or diagonally connected components on the grid.
Depending on `hierarchical`, the list is either a flat list of all objects or hierarchical list where each items is a dict with a `children` key. Either way, an object contain an `obj` key with `list[tuple[tuple[int,int],int]]` as the values.
An option is also available to describe irregular objects as a set of rectangles or lines under the key `'as_rectangles'`
- `move_object(obj: Object, tl_yx: tuple[int, int]=(0, 0)) -> Object` that creates an object where the top-left corner of the *bounding box* of the object is changed.
- `flood_fill(obj: Object, color: int) -> Object` that flood fills an object (this function fills holes of the object as well, to only change the color of an object use Python code such as list comprehension)
- `put_obj_on_grid(grid: Grid, obj: Object, clip: bool=True) -> None` that puts an object on a grid
- `direct_neighbors(loc: tuple[int,int]) -> Indices`
- `diagonal_neighbors(loc: tuple[int,int]) -> Indices`
- `neighbors(loc: tuple[int,int]) -> Indices`
- `most_common_color(element: Object|Grid) -> int`
- `get_obj_colors(obj: Object) -> set[int]`


**VERY IMPORTANT NOTE**
This is part of an developer-unaware-intelligence AGI benchmark. This means that developer, that is me, cannot anticipate what tools you need to solve all tasks.
For example, the obove-mentioned object detection/description functions might not be appropriate or sufficiet for some of the tasks; I have provided only
an examplar toolset. The problems vary in difficualty, but are generally simple for humans (over 80% are solved by over 80% of people in a study). So, don't feel
an urge to complicate the matter, make use of all tools provided, or assume that I promote (or demote, for that matter) using them.


Other notes:
- Your `solve` function should accept each grid as a Python list of lists. Each element of the list represents one color as an integer from 0 to 9.
- The color mappings are: black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, light blue: 8, brown: 9.
- Remember that the inputs and outputs are row-major encoded.
- Put your functions with the provided signatures in a code block. If you need you can write other functions as well. Statements other than function definitions and imports will be commented out.
- Do not assume the existence of other functions in the executation context. Do not provide mock implentation of any function. Avoid mock implementations. Avoid placeholder implementations.

Good luck!
'''
            ],
            do_work=self.extract_and_run_mapping_code,
            llm=lambda: LLMInterface.TEXT_ADVANCED,
            next_state=lambda response: 'success' if self.is_last_run_success() else 'mapping_code_failed'
        )

        self.states['mapping_code_failed'] = dict(
            pre_work=self.mapping_code_failed_work,
            message_to_send=[
                lambda: ('list', self.send_last_run_results())
            ],
            do_work=self.extract_and_run_mapping_code,
            llm=lambda: LLMInterface.TEXT_ADVANCED,
            message_ttl=lambda: [2,2],
            next_state=lambda response: self.mapping_code_failed_next_state(response)            
        )

        self.states['success'] = dict(
            pre_work=self.extract_and_save_solution,
            next_state=None
        )

        self.states['total_failure'] = dict(
            next_state=None
        )

    def mapping_code_failed_work(self):
        self.num_failed += 1

    def extract_and_run_mapping_code(self, response):
        # tools_codes = '\n'.join(v['code'] for v in self.tools.values())
        tools_codes = Path(current_file_dir / 'tools_src_mini.py').read_text()
        
        results = extract_and_run_mapping_code(response, self.task_id, self.dataset, tools_code=tools_codes)
        self.run_results.append(results)

    def send_all_pairs(self, with_descriptors: bool):
        results = []
        pair_indices = self.which_pairs
        if self.which_pairs == 'all':
            pair_indices = range(len(self.task['train']))
        if self.distinct_pairs:                        
            for i, pair_index in enumerate(pair_indices): 
                if len(pair_indices) > 1:
                    results.append(('text', f'Pair {i+1}'))
                grid = self.task['train'][pair_index]['input']
                results.append(('image', single_grid_to_base64(grid,
                    draw_edges=False, draw_spine_border=True)))
                if with_descriptors and self.default_input_grid_lens is not None:
                    results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(grid)}`'))
                
                grid = self.task['train'][pair_index]['output']
                results.append(('image', single_grid_to_base64(grid,
                    draw_edges=False, draw_spine_border=True)))
                if with_descriptors and self.default_input_grid_lens is not None:
                    results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(grid)}`'))
        else:
            all_in_one_arg = [self.task['train'][i] for i in pair_indices]
            results.append('image',
                    grids_all_in_one_to_base64(all_in_one_arg, draw_edges=False, draw_spine_border=True))
        return results
    

    
    def is_last_run_success(self):
        return (
            len(self.run_results) >= 1 and
            len(self.run_results[-1]) >= 2 and
            'text' in self.run_results[-1][-2] and
            self.run_results[-1][-2]['text'] == '|successful run|' # last_run's all-but-last message
        )

    def extract_and_save_solution(self):
        self.solution = eval(self.run_results[-1][-1]['text']) # last_run's last message

    def mapping_code_failed_next_state(self, response):
        if self.is_last_run_success():
            return 'success'
        elif self.num_failed < self.max_num_failed:
            return 'mapping_code_failed'       
        return 'total_failure'

    def send_last_run_results(self):
        results = []
        for obj in self.run_results[-1]:
            if 'text' in obj:
                results.append(('text', obj['text']))
            elif 'grid' in obj:
                grid = obj['grid']
                # these are pruned later, because the llm is text-advanced
                results.append(('image', single_grid_to_base64(grid, draw_edges=False, draw_spine_border=True)))
                if self.default_input_grid_lens is not None: # TODO: change grid to grid-input, etc and use self.default_paired_grid_lens
                    results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(grid)}`'))
                    if self.monochromatic_useful and self.monochromatic_bg:                        
                        results.append(('text', f'mono chromatic version of this image where {color_to_str(self.monochromatic_bg)} is replaced with black and all other colors to yellow:'))
                        mc_grid = make_grid_monochrome(grid, color_to_bg=self.monochromatic_bg)
                        # these are pruned later, because the llm is text-advanced
                        results.append(('image', single_grid_to_base64(mc_grid, draw_edges=False, draw_spine_border=True)))
                        results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(mc_grid)}`'))
                
        # if any_grid_description_added:
        #     results.append(('text', f'\n\nNote: Grid descriptions created using `{self.default_input_grid_lens_code}`.'))
        
        return results

    def send_grid_(self, grid, with_descriptors: bool) -> tuple[bool, list[tuple[str,str]]]:
        # print(f'send_grid_: {with_descriptors=}')
        any_grid_description_added = False
        results = []
        results.append(('image', single_grid_to_base64(grid, draw_edges=False, draw_spine_border=True)))
        if with_descriptors and self.default_input_grid_lens is not None: # TODO: change grid to grid-input, etc and use self.default_paired_grid_lens
            any_grid_description_added = True
            results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(grid)}`'))
            # print(f'send_grid_: {with_descriptors=} (added desc)')
            if self.monochromatic_useful and self.monochromatic_bg:                        
                results.append(('text', f'mono chromatic version of this image where {color_to_str(self.monochromatic_bg)} is replaced with black and all other colors to yellow:'))
                mc_grid = make_grid_monochrome(grid, color_to_bg=self.monochromatic_bg)
                results.append(('image', single_grid_to_base64(mc_grid, draw_edges=False, draw_spine_border=True)))
                results.append(('text', f'`{self.default_input_grid_lens_code}={self.default_input_grid_lens(mc_grid)}`'))
        
        return any_grid_description_added, results
    
    
    def set_hypothesis_and_get_tools(self, response):        
        self.hypothesis = response

        # self.tools = tools_example
        # return
            
        # FIXME: pass log_dir to statemachine __init__ functions and create a new log file in it
        # log_dir = Path('logs-etc') / 'toolwriter' / datetime.now().strftime('%Y%m%d-%H%M%S')
        # log_file = log_dir / '1.md'
        # log_dir.mkdir(parents=True, exist_ok=True)
        # # llm_tool_writer_ = LLMToolWriter(log_file=log_file)
        # self.tools = llm_tool_writer_(self.hypothesis)
       
    # def send_tools_docs(self):
    #     return generate_tools_docs_by_ast(Path(current_file_dir / 'tools_src_mini.py'), tool_type='all')

    def grid_to_lens_str_human_readable(self, grid, parse_type: str, diagonal: bool=None, with_bg: bool=None, object_describer: str=None):
        assert parse_type in ['objects', 'vlines', 'hlines']
        if parse_type == 'objects':
            objs = parse_grid_as_objects(grid, univalued=True, diagonal=diagonal, with_bg=with_bg, bg_color=self.bg_color, hierarchical=True, object_describer=object_describer)
            descs_str = parsed_things_to_str(objs)
        else: # vlines, hlines
            # FIXME: description
            lines = parse_grid_as_lines(grid, direction='vertical' if parse_type == 'vlines' else 'horizontal')
            descs_str = parsed_things_to_str(lines)
        
        return descs_str
    
    def grid_to_lens_str_json(self, grid, parse_type: str, diagonal: bool=None, with_bg: bool=None, object_describer: str=None):
        assert parse_type in ['objects', 'vlines', 'hlines']
        if parse_type == 'objects':
            objs = parse_grid_as_objects(grid, univalued=True, diagonal=diagonal, with_bg=with_bg, bg_color=self.bg_color, hierarchical=True, object_describer=object_describer)
            descs_str = parsed_things_to_str_json(objs)
        else: # vlines, hlines
            lines = parse_grid_as_lines(grid, direction='vertical' if parse_type == 'vlines' else 'horizontal')
            descs_str = parsed_things_to_str_json(lines)
        
        return descs_str
        
    def select_descriptor(self, response):
        code_blocks = re.findall(r'```(?:json|js|javascript)?\n(.*?)```', response, re.DOTALL)
        for code_block in reversed(code_blocks):
            try:
                obj = json.loads(code_block)
                if 'chosen_descriptor' not in obj:
                    continue
                chosen_descriptor_id = obj['chosen_descriptor']
                desc_dict = next((desc_dict for desc_dict in self.descriptors if desc_dict['id'] == chosen_descriptor_id), None)
                if desc_dict:
                    self.default_input_grid_lens = self.default_output_grid_lens = desc_dict['func']
                    self.default_input_grid_lens_code = self.default_output_grid_lens_code = desc_dict['code'].replace('{self.bg_color}', color_to_str(self.bg_color).upper())

                self.monochromatic_useful = obj.get('monochromatic_useful', None)
                monochromatic_bg = obj.get('monochromatic_bg', None)
                if monochromatic_bg:
                    self.monochromatic_bg = str_to_color(monochromatic_bg.lower())
                other_useful_descriptors = obj.get('other_useful_descriptors', None)
                if other_useful_descriptors:
                    print(f'Useful descriptor for task {self.task_id}: {other_useful_descriptors}')
                return
            except:
                pass

    def send_descriptors(self) -> str:
        results = []
        for descriptor in self.descriptors:
            result = f'''- `{descriptor['id']}`: {descriptor['desc']}'''
            results.append(result)

        return '\n'.join(results)
    
    def send_larc_description(self) -> str:
        df = pd.read_csv('larc_parsed.csv', index_col='task_id')
        return '\n'.join(df.loc[self.task_id])