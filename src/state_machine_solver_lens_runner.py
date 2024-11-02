import sys
import traceback

from task_utils import read_task

class LensRunner:

    def __init__(self, task_id, dataset, code):
        self.messages = []
        self.task = read_task(task_id, dataset)
        self.code = code

    def start_running(self):
        self.run_code(self.code, self.task)
        return "\n".join(self.messages)

    def add_text_to_content(self, message):
        self.messages.append(message)
        print(message)

    def run_code(self, code: str, task: dict):  # TODO run task in another thread or process for a limited amount of time
        err_content = []
        try:
            local_namespace = {}
            exec(code, {}, local_namespace)
        except Exception:
            error_msg = traceback.format_exc()
            self.add_text_to_content (f'''
            The following error happened when evaluating your function `solve`:
            \n{error_msg}\n'
            Please write a corrected code enclosed in triple backticks.''')
        functions = {}
        for function_name, function in local_namespace.items():
            if callable(function):
                functions[function_name] = function
        if len(functions) == 0:
            self.add_text_to_content ('''
            No function was found in the provided code.
            ''')
        else:
            self.run_all_functions(functions)

    def run_all_functions(self, functions):
        for function_name, function in functions.items():
            self.run_function_on_all_grids(function_name, function)

    def run_function_on_all_grids(self, name, function):
        for i, pair in enumerate(self.task['train'], 1):
            self.run_lens_function_on_one_grid(function, i, name, pair['input'], 'input')
            self.run_lens_function_on_one_grid(function, i, name, pair['output'], 'input')

    def run_lens_function_on_one_grid(self, function, i, name, grid, in_or_out):
        try:
            result = function(grid)
            self.add_text_to_content(f'running {name} on {in_or_out} {i} and the result is {result}')
        except Exception as e:
            error_msg = traceback.format_exc()
            self.add_text_to_content((f'The following error happened when running the function {name} on the {in_or_out} {i}:'
                                      f'\n{error_msg}\n'
                                      f'The input was: {grid}'))



if __name__ == "__main__":
    task_id_ = str(sys.argv[1])
    dataset_ = str(sys.argv[2])
    contents = []
    while True: # i.e., while EOFError has not encountered (where it is sent?)
        try:
            contents.append(input())
        except EOFError:
            break

    code_ = "\n".join(contents)

    code_runner = LensRunner(task_id_, dataset_, code_)
    code_runner.start_running()