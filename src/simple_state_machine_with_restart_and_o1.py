from grid_utils import get_grid_sizes
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from state_machine_solver_utils import extract_and_run_mapping_code

class SimpleStateMachineWithRestartAndO1:
    def __init__(self, task_id, dataset, weak_llm='o1-mini', o1_llm='o1-mini'):
        self.start_state = 'entry_point'
        self.phase = 'all_in_one'
        self.states = {}
        self.dataset = dataset
        self.run_results = []
        self.task_id = task_id
        self.task = dataset.read_task(task_id)
        self.solution = None
        self.max_num_failed = 2
        self.num_failed = 0
        self.weak_llm = weak_llm
        self.o1_llm = o1_llm
        self.summary_for_o1 = None

        # starting with all-images (no bordrer), looking to features, ...
        self.states['entry_point'] = dict(
            message_to_send=[
                lambda: 'The following image shows examples of mapping from an input grid (left) to an output grid (right):',
                lambda: ('image', grids_all_in_one_to_base64(self.task['train'], draw_edges=False)),
                lambda: f'''Please write a Python function with the signature `solve(grid: list[list[int]]) -> list[list[int]]`
that maps the left images to the right images. Note that the inputs and outputs are row-major encoded.

Notes:
- Your function should accept each grid as a Python list of lists. Each element of the list represents one
color as an integer from 0 to 9. The color mappings are:
black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, teal: 8, brown: 9.
- Please first explain what you see in the input and output images, noticing to
object (points, lines, squares, zones, patches, etc) and their properies (position, color, thickness, etc)
and then write the code.
- Note that the attached images do not display their actual resolutions. For instance, what appears to be
a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple
smaller cells. The maximum grid size is 30x30. {get_grid_sizes(self.task, which='all')}
- Put your solve function with the provided signature in a code block, I will run your code and
let you know the results.'''
            ],
            llm=lambda: self.weak_llm,
            do_work=self.extract_and_run_mapping_code,
            next_state=lambda response: 'success' if '<successful run>' in self.run_results[-1] else 'mapping_code_failed'
        )

        self.states['mapping_code_failed'] = dict(
            pre_work=self.mapping_code_failed_work,
            message_to_send=[
                lambda: ('list', self.send_last_run_results())
            ],
            llm=lambda: self.weak_llm if self.phase != 'o1' else self.o1_llm,
            do_work=self.extract_and_run_mapping_code,
            next_state=lambda response: self.mapping_code_failed_next_state(response)
        )

        self.states['send_first_pair'] = dict(
            pre_work=self.send_first_pair_pre_work,
            message_to_send=[
                lambda: '''It seems that your code didn't work after several retries.
Now, I attach the first pair of input and output images seperately. This hopefully helps you better see the images.''',
                lambda: ('image', single_grid_to_base64(self.task['train'][0]['input'], draw_edges=False)),
                lambda: ('image', single_grid_to_base64(self.task['train'][0]['output'], draw_edges=False)),
                lambda: f'''Please write a Python function with the signature `solve(grid: list[list[int]]) -> list[list[int]]`
that maps the input image to the output image. Note that the inputs and outputs are row-major encoded.

Notes:
- Your function should accept each grid as a Python list of lists. Each element of the list represents one
color as an integer from 0 to 9. The color mappings are:
black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, teal: 8, brown: 9.
- Please first explain what you see in the input and output images, noticing to
object (points, lines, squares, zones, patches, etc) and their properies (position, color, thickness, etc)
and then write the code.
- Note that the attached images do not display their actual resolutions. For instance, what appears to be
a 2x2 grid in an image might actually be a 6x6 grid, with each cell of the 2x2 grid comprising multiple
smaller cells. The maximum grid size is 30x30. {get_grid_sizes(self.task, which=1)}
- Put your solve function with the provided signature in a code block, I will run your code and
let you know the results.'''
            ],
            llm=lambda: self.weak_llm,
            next_state=lambda response: 'success' if '<successful run>' in self.run_results[-1] else 'mapping_code_failed'
        )

        self.states['aks_for_o1_summary'] = dict(
            pre_work=self.aks_for_o1_summary_pre_work,
            message_to_send = [
                lambda: '''It seems that this problem is hard for you. Now, I am transferring to a more advanced
LLM. But this LLM is text only and cannot see the images. Please summarize the task, your approach, you best code, and
any other useful information to be passed to this LLM. Overall, I appreciate your attempts to solve this problem.'''
            ],
            do_work=self.aks_for_o1_summary_do_work,
            llm=lambda: self.weak_llm,
            next_state='o1'
        )

        self.states['o1'] = dict(
            message_to_send = [
                lambda: '''Here is a task that I asked a less advanced but multi-modal LLM to solve. It tried its best, but after
several tries, I concluded that task is hard for it.

## Original task description:''',
                lambda: self.states['entry_point']['message_to_send'][0](),
                lambda: f'Sample input as python list of list: {self.task["train"][0]["input"]}',
                lambda: f'Sample output as python list of list: {self.task["train"][0]["output"]}',
                lambda: self.states['entry_point']['message_to_send'][2](),
                lambda: f'''\n\n## A summary written by the multi-modal LLM for you:
\n{self.summary_for_o1}\n
## Your task:
Can you work out the correct code that transforms inputs to the outputs?'''
            ],
            llm=lambda: self.o1_llm,
            do_work=self.extract_and_run_mapping_code,            
            next_state=lambda response: 'success' if '<successful run>' in self.run_results[-1] else 'mapping_code_failed'
        )


        self.states['success'] = dict(
            pre_work=self.extract_and_save_solution,
            next_state=None
        )

        self.states['total_failure'] = dict(
            next_state=None
        )

    def send_first_pair_pre_work(self):
        self.num_failed = 0
        self.phase = 'first_pair'

    def aks_for_o1_summary_pre_work(self):
        self.phase = 'o1'

    def aks_for_o1_summary_do_work(self, response):
        self.summary_for_o1 = response

    def mapping_code_failed_work(self):
        self.num_failed += 1

    def extract_and_run_mapping_code(self, response):
        results = extract_and_run_mapping_code(response, self.task_id, self.dataset)
        self.run_results.append(results)

    def extract_and_save_solution(self):
        self.solution = eval(self.run_results[-1].split('<successful run>')[1])

    def mapping_code_failed_next_state(self, response):
        if '<successful run>' in self.run_results[-1]:
            return 'success'
        elif self.num_failed < self.max_num_failed:
            return 'mapping_code_failed'
        elif self.phase == 'all_in_one':
            return 'send_first_pair'
        elif self.phase == 'first_pair':
             return 'aks_for_o1_summary'
        else: # o1
            return 'total_failure'

    def send_last_run_results(self):
        results = []
        for obj in self.run_results[-1]:
            if 'text' in obj:
                results.append(('text', obj['text']))
            elif 'grid' in obj:
                results.append(('image', single_grid_to_base64(obj['grid'], draw_edges=False)))
        return results