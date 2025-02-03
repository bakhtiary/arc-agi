from datetime import datetime
import json
from pathlib import Path
import re
import pandas as pd
from code_utils import generate_tools_docs_by_ast
from dataset import Dataset
from grid_utils import get_grid_sizes, AKGrid
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from llm_utils import HistoryManager, LLMInterface, chat_with_llm
from state_machine_solver_utils import extract_and_run_mapping_code
from tools_src_mini import BLACK, BROWN, color_to_str, make_grid_monochrome, parse_grid_as_lines, parse_grid_as_objects, parsed_single_thing_to_str, parsed_things_to_str, parsed_things_to_str_json, str_to_color

current_file_dir = Path(__file__).parent

def callable_as_list(obj):
    if isinstance(obj, list):
        return obj
    else:
        assert callable(obj)
        return [obj]

class SimpleStateMachineWithToolsAndFixedHypo:
    """
        workflow: entry_point
            --> ask_for_code (`solve`, hardcoded tools)
    """
    def __init__(self, task_id, dataset: Dataset, distinct_pairs=True, which_pairs: str|list[int]='all'):
        self.start_state = 'entry_point'
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

        self.states['entry_point'] = dict(
            message_to_send=[
                lambda: f'''The final goal of this conversation is to that you write a Python function that successfully maps the input grids to the output grids.
Here is a description of the grids: {self.hypothesis}

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

    def send_all_pairs(self):
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
               
                grid = self.task['train'][pair_index]['output']
                results.append(('image', single_grid_to_base64(grid,
                    draw_edges=False, draw_spine_border=True)))
                
        else:
            all_in_one_arg = [self.task['train'][i] for i in pair_indices]
            results.append('image',
                    grids_all_in_one_to_base64(all_in_one_arg, draw_edges=False, draw_spine_border=True))
        return results
    

    def send_pairs(self):
        pairs = []
        pair_indices = self.which_pairs
        if self.which_pairs == 'all':
            pair_indices = range(len(self.task['train']))
        if self.distinct_pairs:                        
            for i, pair_index in enumerate(pair_indices): 
                if len(pair_indices) > 1:
                    pairs.append(('text', f'Pair {i+1}'))
                pairs.append(('image',
                    single_grid_to_base64(self.task['train'][pair_index]['input'], draw_edges=False, draw_spine_border=True)))
                pairs.append(('image',
                    single_grid_to_base64(self.task['train'][pair_index]['output'], draw_edges=False, draw_spine_border=True)))
                # if self.default_single_grid_lens:
                #     pairs.append(('text', self.default_single_grid_lens(grid)))
        else:
            all_in_one_arg = [self.task['train'][i] for i in pair_indices]
            pairs.append('image',
                    grids_all_in_one_to_base64(all_in_one_arg, draw_edges=False, draw_spine_border=True))
        return pairs


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
                
        return results

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



    def add_state_machine_messages(self, cur_state_messages, llm: str, history_manager: HistoryManager, tst=None):
        any_message_added = False
        with history_manager.start_new_message('user', llm, tst=tst):                    
            state_message_funcs = callable_as_list(cur_state_messages)
            for state_message_func in state_message_funcs:
                state_message_ret = state_message_func()
                if isinstance(state_message_ret, tuple):
                    state_message_type, state_message = state_message_ret
                else:
                    state_message_type, state_message = 'text', state_message_ret
                        
                assert state_message_type in ['image', 'text', 'list']
                if state_message_type == 'image':
                    history_manager.add_image(state_message)
                    any_message_added = True
                elif state_message_type == 'text':
                    history_manager.add_text(state_message)
                    any_message_added = True
                elif state_message_type == 'list': # state_message itself is a list of tuples
                    for state_message_type, state_message  in state_message:
                        assert state_message_type in ['image', 'text']
                        if state_message_type == 'image':
                            history_manager.add_image(state_message)
                            any_message_added = True
                        elif state_message_type == 'text':
                            history_manager.add_text(state_message)
                            any_message_added = True
        
        return any_message_added
    
    def get_hypos(self, llm_interface: LLMInterface, log_file = None, num_hypos=1) -> list[str]:
        history_manager = HistoryManager(log_file)
    
        # examples by:
        #   df['Concatenated'] = df.iloc[:, 1].astype(str) + ' ' + df.iloc[:, 2].astype(str) + ' ' + df.iloc[:, 3].astype(str)
        #   print(df[['Concatenated']].head(10).to_string(index=False, header=False))
        message_to_send =[
                lambda: 'The following images shows examples of a mapping from an input grid to the output grid:',
                lambda: ('list', self.send_pairs()),
                lambda: f'''Please examine the images and explain in detail what transformations or patterns you observe between the input and output grids.

Notes:
- Notice objects such as points, lines, squares, zones, sections, patches, etc., and their properties (position, color, thickness, etc.).
- Keep in mind that the attached images do not display their actual resolutions. For instance, what appears to be a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple smaller cells.
- The maximum grid size is 30x30. {get_grid_sizes(self.task, which='all')}
- After providing your explanation, I will ask you to write code to implement the mapping.
- Respond with a json (in a code block) list of strings where each string is a hypothesis. Generate {num_hypos} hypotheses.

Some examples (not for the task at hand, but to give you an idea of how your description needs to be. PLEASE MAKE SURE ALL HYPOTHESIS ARE RELEVANT TO THE IMAGES ABOVE)
In the input, you should see a 3x3 grid with four boxes in black and five boxes in a different color The output grid size does not change but the grid is not segmented into small boxes. To make the output, you have to consider the pattern of the colored boxes. where the colored boxes form a cross, the output color should be pink.where there are three colored boxes at the top left corner the output color should be blue. Where there are four colored boxes at the top right the output color should be green. Where the colored boxes are at the middle of each of the first and third column and in the middle column the colored boxes are at the top and bottom, the output color should be red.
In the input, you should see a long grid with several colors The output grid size 4 by 4 To make the output, you have to join the upper and lower into one design, leaving the black spaces black and the other colors now green
In the input, you should see shapes with black inside and dot in center The output grid size match the output To make the output, you have to color the inside blue but if the border of shape goes outside the grid leave inside black
In the input, you should see several blue squares placed at different parts The output grid size should be the same size as the input grid To make the output, you have to place a orange square to the space left of any blue square, a red square in the space above any blue square, a purple square to the space on the right of any blue square and a light blue square to the space below any blue square.
In the input, you should see a large grid with shapes of three different colors on a colored background The output grid size is the same as the input grid To make the output, you have to remove the small shape and replicate it over each block of the same color as its center and color in the row or column of the blocks that extend from the shape to the edge of the colored area it is within for the blocks around the center of the small shape that are two blocks wide or two blocks tall and touch the sides of the center of the shape
In the input, you should see  3 shapes of blue, red, and yellow colors. The output grid size is the same size as the input grid To make the output, you have to keep the blue shape where it is, and move the red and yellow shapes up or down so that they are at the same level as the blue-colored shape.
In the input, you should see two patterns on top of one another with a line dividing them The output grid size size of one pattern To make the output, you have to overlapping the two patterns, if the colors are the same then it is colored black. if they are different then they are colored in a different color
In the input, you should see .a 3x3 grid with black and pink squares. There colors are the same for each input grid but the site of the colors are different. The output grid size a 1x1 grid To make the output, you have to .fill in the first, second and last with blue and fill in the other three with yellow.
In the input, you should see a grid with a square or rectangle composed of monochromatic pixels with a colored pixel at each of the interior corners of the rectangle. The output grid size  is the same as the input. To make the output, you have to   copy the input grid to the output workspace.  Move each of the interior corner colored pixels to the exterior corner opposite of their input position.  Meaning, move the upper left interior pixel such that its corner is touching the lower left corner of the lower left corner pixel of the monochromatic rectangle or square.  You're moving pixel at a 45 degree angle to the exterior opposite corner, do that with each interior corner square to create the correct output grid.
In the input, you should see four colored lines that form either a square or rectangular shape in the middle of the black background with colored squares in it. The output grid size is the same as the size of the square or rectangle shape in the middle of the black background that is formed by the four colored lines. To make the output, you have to change the grid size to just the square or rectangle formed by the four colored lines. Then look at the random dots in the middle of the square or rectangle. Find the colored border that matches the color of the dots, using that color, you will connect each dot to that border in a straight line. You should have 3 to four straight lines touching the matching border.
'''
        ]

        any_message_sent = self.add_state_machine_messages(
            message_to_send, LLMInterface.VISION, history_manager)                
        response = chat_with_llm(llm_interface, history_manager, LLMInterface.VISION)
        history_manager.add_singletone_text_message('assistant', response, LLMInterface.VISION)
        a_json_str = re.findall(r'```(?:json)?\n(.*?)```', response, re.DOTALL)[0]
        a_json = json.loads(a_json_str)
        assert isinstance(a_json, list)
        return a_json
