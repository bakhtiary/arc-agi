from grid_utils import get_grid_sizes
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from state_machine_solver_utils import extract_and_run_mapping_code

"""
Analysing these three logs:
    - 20240928-204119 (not_in_results_json: 0, success_ok: 41, n/a: 359, a)
    - 20240929-194035 (not_in_results_json: 11, success_ok: 30, n/a: 293, b)
    - 20241106-230542 (not_in_results_json: 0, success_ok: 15, success_nok: 1, timeout: 11, c)

That is:
Score: 2.00 (17: a=15, b=10, c=9)
91714a58 (a, b, c) 50cb2852 (a, b, c) 4347f46a (a, c) a61f2674 (a, b, c) 85c4e7cd (a, b, c) a2fd1cf0 (a, b) b60334d2 (a, c) d511f180 (a, b, c) e98196ab (a, c) 56ff96f3 (a, b, c) 23581191 (a, b) b1948b0a (a, b) b6afb2da (a, b) 4258a5f9 (a, b) e9afcf9a (a, b) d23f8c26 (a, b) 42a50994 (a, b)
Score: 1.00 (31: a=18, b=12, c=1)
ea786f4a (a, b) beb8660c (a, c) 4be741c5 (a, b) c59eb873 (a) 5582e5ca (a, b) d0f5fe59 (a, b, c) d364b489 (a, b) 49d1d64f (a, b, c) 6f8cd79b (a, b) be94b721 (a) 5614dbcf (a, b) aedd82e4 (a, b) c9f8e694 (a, b) 1f876c06 (a) 445eab21 (a, b) 68b16354 (a, b) aabf363d (a) a699fb00 (a, b) a416b8f3 (a, b) bdad9b1f (a, b) 9172f3a0 (a) f25ffba3 (a, b) 253bf280 (a, b) 3618c87e (a, b) 1cf80156 (a, b) 2dee498d (a, b) bb43febb (a, b) d631b094 (a, b, c) a740d043 (a) dc1df850 (a, b) a9f96cdd (a, b)

Shows that: there are several cases that o1-method acts as a union of the two, however, there is
no single case that this method solves a problem unsolved by that union. So, if it's a way to combine the
two in an organic and efficient way, there is no need to consult pricy o1.
"""

class SimpleStateMachineWithO1:
    def __init__(self, task_id, dataset, weak_llm='gpt-4o', o1_llm='o1-mini'):
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
            next_state=lambda response: 'success' if self.is_last_run_success() else 'mapping_code_failed'
        )

        self.states['mapping_code_failed'] = dict(
            pre_work=self.mapping_code_failed_work,
            message_to_send=[
                lambda: ('list', self.send_last_run_results())
            ],
            llm=lambda: self.weak_llm if self.phase != 'o1' else self.o1_llm,
            do_work=self.extract_and_run_mapping_code,
            message_ttl=lambda: [1,1],
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
            next_state=lambda response: 'success' if self.is_last_run_success() else 'mapping_code_failed'
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
            next_state=lambda response: 'success' if self.is_last_run_success() else 'mapping_code_failed'
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