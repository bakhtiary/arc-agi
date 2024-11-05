from dataset import Dataset
from image_utils import grids_all_in_one_to_base64
from state_machine_solver_utils import extract_and_run_mapping_code, extract_and_run_lens_code


class SimpleStateMachine:
    def __init__(self, task_id, dataset: Dataset):
        self.start_state = "entry_point"
        self.states = {}
        self.dataset = dataset
        self.run_results = []
        self.task_id = task_id
        self.task = dataset.read_task(task_id)
        self.solution = None
        self.states["entry_point"] = dict(
            message_to_send=[
                lambda: '''The following image shows examples of mapping from an input grid (left) to an output grid (right)
the inputs (left) and the outputs (right)''',
                lambda: ('image', grids_all_in_one_to_base64(self.task['train'])),
                lambda: '''Please write a python function with the signature `solve(grid : list[list[int]]) -> list[list[int]]`
that maps the left images to the right images. Note that the inputs and outputs are row major encoded.
Your function should accept each grid as a Python list of lists. Each element of the list represents one color as an integer 
from 0 to 9. The color mappings are: black: 0, blue: 1, red: 2, green: 3, yellow: 4, grey: 5, magenta: 6, orange: 7, teal: 8, brown: 9.'''
            ],
            next_state=lambda response: "success" if self.extract_and_run_mapping_code_works(response) else "total_failure"
        )
        self.states["success"] = dict(
            do_work=self.extract_and_save_solution,
            next_state=None
        )
        self.states["total_failure"] = dict(
            next_state=None
        )

    def extract_and_run_mapping_code_works(self, response):
        result = extract_and_run_mapping_code(response, self.task_id, self.dataset)
        self.run_results.append(result)
        return "<successful run>" in result

    def extract_and_save_solution(self, response):
        self.solution = eval(self.run_results[-1].split("<successful run>")[1])