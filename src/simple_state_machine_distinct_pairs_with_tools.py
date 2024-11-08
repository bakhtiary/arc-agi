from datetime import datetime
from pathlib import Path
from grid_utils import get_grid_sizes
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from llm_tool_writer import LLMToolWriter
from state_machine_solver_utils import extract_and_run_mapping_code
from tools_example import tools_example


class SimpleStateMachineDistinctPairswithTools:
    def __init__(self, task_id, dataset):
        self.start_state = 'entry_point'
        self.phase = 'all_in_one'
        self.states = {}
        self.dataset = dataset
        self.run_results = []
        self.task_id = task_id
        self.task = dataset.read_task(task_id)
        self.solution = None
        self.max_num_failed = 5
        self.num_failed = 0
        self.which_pairs = 'all'
        
        # starting with all-images (no bordrer), looking to features, ...
        self.states['entry_point'] = dict(
            message_to_send=[
                lambda: 'The following images shows an example of a mapping  from an input grid to the output grid:',
                lambda: ('list', self.send_pairs()),
                lambda: f'''Please examine the images and explain in detail what transformations or patterns you observe between the input and output grids.

Notes:
- Notice objects such as points, lines, squares, zones, patches, etc., and their properties (position, color, thickness, etc.).
- Keep in mind that the attached images do not display their actual resolutions. For instance, what appears to be a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple smaller cells.
- The maximum grid size is 30x30. {get_grid_sizes(self.task, which='all')}
- After providing your explanation, I will ask you to write code to implement the mapping.'''
            ],
            do_work=self.set_hypothesis_and_get_tools,
            next_state='ask_for_code'
        )

        self.states['ask_for_code'] = dict(
            message_to_send=[
                lambda: f'''Based on your explanation, please write a Python function with the signature `solve(grid: list[list[int]]) -> list[list[int]]` that implements your proposed mapping.

Available function that you can use:
{self.send_tools_docs()}

Notes:
- Your function should accept each grid as a Python list of lists. Each element of the list represents one color as an integer from 0 to 9.
- The color mappings are: black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, teal: 8, brown: 9.
- Remember that the inputs and outputs are row-major encoded.
- Put your solve function with the provided signature in a code block. I will run your code and let you know the results.'''
            ],
            do_work=self.extract_and_run_mapping_code,
            next_state=lambda response: 'success' if self.is_last_run_success() else 'mapping_code_failed'
        )

        self.states['mapping_code_failed'] = dict(
            pre_work=self.mapping_code_failed_work,
            message_to_send=[
                lambda: ('list', self.send_last_run_results())
            ],
            do_work=self.extract_and_run_mapping_code,
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
        tools_codes = '\n'.join(v['code'] for v in self.tools.values())
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

        # self.tools = tools_example
        # return
            
        # FIXME: pass log_dir to statemachine __init__ functions and create a new log file in it
        log_dir = Path('logs-etc') / 'toolwriter' / datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = log_dir / '1.md'
        log_dir.mkdir(parents=True, exist_ok=True)
        llm_tool_writer_ = LLMToolWriter(log_file=log_file)
        self.tools = llm_tool_writer_(self.hypothesis)

    def send_tools_docs(self):
        results = ''
        for func_name, v in self.tools.items():
            results += f'- {v["signature"]}\n'
        return results