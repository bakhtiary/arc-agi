import json
import traceback

class CodeRunner:
    def start_running(self, code):
        self.do_run_code(code)

    def emit_text(self, message):
        print(json.dumps({'text': message}))

    def emit_grid(self, grid):
        print(json.dumps({'grid': grid}))

    def do_run_code(self, code: str):
        try:
            local_namespace = {}
            exec(code, local_namespace)
        except Exception:
            error_msg = traceback.format_exc()
            self.emit_text (f'''The following error happened when evaluating your code:
\n{error_msg}\n'
Please write a corrected code enclosed in triple backticks.''')
            return ## Is this correct?

#         if 'solve' not in local_namespace:
#             self.emit_text ('''Function `solve` is not defined.
# Please try again and make sure the code is enclosed in triple backticks.''')
#             return
        
        self.emit_text('|successful run|')

if __name__ == "__main__":
    contents = []
    while True: # i.e., while EOFError has not encountered (where it is sent?)
        try:
            contents.append(input())
        except EOFError:
            break

    code_ = '\n'.join(contents)

    code_runner = CodeRunner()
    code_runner.start_running(code_)