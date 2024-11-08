from grid_utils import get_grid_sizes
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from state_machine_solver_utils import extract_and_run_mapping_code


class SimpleStateMachineSinglePair:
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

        # starting with all-images (no bordrer), looking to features, ...
        self.states['entry_point'] = dict(
            message_to_send=[
                lambda: 'The following images shows an example of a mapping  from an input grid to the output grid:',
                lambda: ('image', single_grid_to_base64(self.task['train'][0]['input'], draw_edges=False, draw_spine_border=True)),
                lambda: ('image', single_grid_to_base64(self.task['train'][0]['output'], draw_edges=False, draw_spine_border=True)),
                lambda: f'''Please examine the images and explain in detail what transformations or patterns you observe between the input and output grids.

Notes:
- Notice objects such as points, lines, squares, zones, patches, etc., and their properties (position, color, thickness, etc.).
- Keep in mind that the attached images do not display their actual resolutions. For instance, what appears to be a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple smaller cells.
- The maximum grid size is 30x30. {get_grid_sizes(self.task, which='all')}
- After providing your explanation, I will ask you to write code to implement the mapping.'''
            ],
            next_state='ask_for_code'
        )

        self.states['ask_for_code'] = dict(
            message_to_send=[
                lambda: '''Based on your explanation, please write a Python function with the signature `solve(grid: list[list[int]]) -> list[list[int]]` that implements your proposed mapping.

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
        results = extract_and_run_mapping_code(response, self.task_id, self.dataset)
        self.run_results.append(results)

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