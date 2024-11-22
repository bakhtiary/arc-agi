from datetime import datetime
from pathlib import Path
from code_utils import generate_tools_docs_by_ast
from grid_utils import get_grid_sizes, AKGrid
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from llm_tool_writer import LLMToolWriter
from llm_utils import LLMInterface
from state_machine_solver_utils import extract_and_run_mapping_code
from tools_example import tools_example

current_file_dir = Path(__file__).parent

class SimpleStateMachineDistinctPairswithTools:
    def __init__(self, task_id, dataset, which_pairs: str|list[int]='all'):
        self.start_state = 'entry_point'
        self.phase = 'all_in_one'
        self.states = {}
        self.dataset = dataset
        self.run_results: list[list[dict]] = [] # each run result is a list of dicts such as [{'text': xx}, {'grid': [[1]]}, ...]
        self.task_id = task_id
        self.task = dataset.read_task(task_id)
        self.solution: list[AKGrid] = None # one solution for each test case
        self.max_num_failed = 10
        self.num_failed = 0
        self.which_pairs = which_pairs
        self.tools: list[dict]  = None # each tool is a dict {'name': 'f', 'signature': 'def f ...', 'code': 'import xx;\n...'}
        self.hypothesis = None
        
        # starting with all-images (no bordrer), looking to features, ...
        self.states['entry_point'] = dict(
            message_to_send2=[ # <-- remove this in final (should be message_to_send)
                lambda: 'The following images shows an example of a mapping from an input grid to the output grid:',
                lambda: ('list', self.send_pairs()),
                lambda: f'''Please examine the images and explain in detail what transformations or patterns you observe between the input and output grids.

Notes:
- Notice objects such as points, lines, squares, zones, sections, patches, etc., and their properties (position, color, thickness, etc.).
- Keep in mind that the attached images do not display their actual resolutions. For instance, what appears to be a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple smaller cells.
- The maximum grid size is 30x30. {get_grid_sizes(self.task, which='all')}
- After providing your explanation, I will ask you to write code to implement the mapping.'''
            ],
            do_work=self.set_hypothesis_and_get_tools,
            next_state='ask_for_code'
        )

        self.states['ask_for_code'] = dict(
            message_to_send=[
                lambda: self.hypothesis, #<-- remove this in final
                lambda: f'''Based on your explanation, please write a Python function with the signature `solve(grid: list[list[int]]) -> list[list[int]]` that implements your proposed mapping.

Available function that you can use:
{self.send_tools_docs()}


Notes:
- Your function should accept each grid as a Python list of lists. Each element of the list represents one color as an integer from 0 to 9.
- The color mappings are: black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, light blue: 8, brown: 9.
- Remember that the inputs and outputs are row-major encoded.
- Put your solve function with the provided signature in a code block. I will run your code and let you know the results.
- Do not use any other function other than those specified above. Do not implement those functions, with empty bodies for example:
They are available in the executation context.
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
            message_ttl=lambda: [1,1],
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
        
        response = f'```\n{tools_codes}\n```\n\n' + response
        results = extract_and_run_mapping_code(response, self.task_id, self.dataset)
        self.run_results.append(results)

    def send_pairs(self):
        pairs = []
        pair_indices = self.which_pairs
        if self.which_pairs == 'all':
            pair_indices = range(len(self.task['train']))
        
        for i, pair_index in enumerate(pair_indices): 
            if len(pair_indices) > 1:
                pairs.append(('text', f'Pair {i+1}'))
            pairs.append(('image',
                single_grid_to_base64(self.task['train'][pair_index]['input'], draw_edges=False, draw_spine_border=True)))
            pairs.append(('image',
                single_grid_to_base64(self.task['train'][pair_index]['output'], draw_edges=False, draw_spine_border=True)))
            
        return pairs

    def is_last_run_success(self):
        return (
            len(self.run_results) >= 1 and
            len(self.run_results[-1]) >= 2 and
            'text' in self.run_results[-1][-2] and
            self.run_results[-1][-2]['text'] == '|successful run|'
        )

    def extract_and_save_solution(self):
        self.solution = eval(self.run_results[-1][-1]['text'])

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
                results.append(('image', single_grid_to_base64(obj['grid'], draw_edges=False, draw_spine_border=True)))
        return results
    
    
    def set_hypothesis_and_get_tools(self, response):        
        self.hypothesis = response 

        # <-- remove this in final
        self.hypothesis = '''To analyze the transformations between the input and output grids, let's break down the observations for each pair:

### Pair 1
- **Input Grid:**
  - Three distinct horizontal color bands: blue (top), yellow (middle), and gray (bottom).
  - Three black squares located in different bands.
- **Output Grid:**
  - Vertical black lines are drawn from the top to the bottom of the grid at the x-coordinates of the black squares in the input grid.

### Pair 2
- **Input Grid:**
  - Two vertical color bands: red (left) and blue (right).
  - Two black squares located in different bands.
- **Output Grid:**
  - Horizontal black lines are drawn from the left to the right of the grid at the y-coordinates of the black squares in the input grid.

### Pair 3
- **Input Grid:**
  - Three horizontal color bands: green (top), red (middle), and blue (bottom).
  - Three black squares located in different bands.
- **Output Grid:**
  - Vertical black lines are drawn from the top to the bottom of the grid at the x-coordinates of the black squares in the input grid.

### Pair 4
- **Input Grid:**
  - Three vertical color bands: red (left), gray (middle), and yellow (right).
  - Three black squares located in different bands.
- **Output Grid:**
  - Horizontal black lines are drawn from the left to the right of the grid at the y-coordinates of the black squares in the input grid.

### General Observations
- The transformation involves drawing lines based on the positions of black squares in the input grid.
- If the grid is divided into horizontal bands, vertical lines are drawn at the x-coordinates of the black squares.
- If the grid is divided into vertical bands, horizontal lines are drawn at the y-coordinates of the black squares.
- The color bands themselves do not change between input and output grids.

These observations suggest a pattern where the type of line (vertical or horizontal) is determined by the orientation of the color bands, and the position of the lines is determined by the coordinates of the black squares.
'''

        # self.tools = tools_example
        # return
            
        # FIXME: pass log_dir to statemachine __init__ functions and create a new log file in it
        # log_dir = Path('logs-etc') / 'toolwriter' / datetime.now().strftime('%Y%m%d-%H%M%S')
        # log_file = log_dir / '1.md'
        # log_dir.mkdir(parents=True, exist_ok=True)
        # # llm_tool_writer_ = LLMToolWriter(log_file=log_file)
        # self.tools = llm_tool_writer_(self.hypothesis)
       
    def send_tools_docs(self):
        return generate_tools_docs_by_ast(Path(current_file_dir / 'tools_src_mini.py'))