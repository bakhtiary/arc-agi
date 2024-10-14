from pathlib import Path
import sys
import traceback
import importlib

from dsl_inspect_utils import generate_dsl_docs_parse
from task_utils import read_task


MAIN_PROMPT = """You want to solve an ARC-like problem (Abstraction and Reasoning Corpus)
by writing a code in a DSL described below. The DSL provides basic operations for
working with ARC grids, such as counting objects or colors, selecting and scaling part
the grid, etc.

# DSL documentation
{dsl_doc}

# Problem statement
Now please solve the following problem (the attached input/output pair) by writing
a program in the above DSL.

# Notes:
- Please strictly adhear to the DSL documentation: your code will be excuted in
a Python runtime that contains the actual definitions of the DSL functions described
above. This is so, because the DSL low level implentation is thoroughly tested, and
you only need to focus on comming up with a high-level solution. 
"""

# TODO:
#   - Add example or examples (few shots)
#   - Ability to declare dsl codes

tool_docs_parse = generate_dsl_docs_parse()
print(tool_docs_parse)

print('Adding arc-dsl to sys.path ...')
sys.path.append('arc-dsl')

dsl_module = importlib.import_module('dsl')
dsl_env_orig = {}
for func_name in dir(dsl_module):
    func = getattr(dsl_module, func_name)
    if callable(func):  # Check if the attribute is a function
        dsl_env_orig[func_name] = func

def verify_dsl_code(code, input_grid, output_grid=None):
    dsl_env = dict(dsl_env_orig)
    dsl_env['I'] = input_grid
    try:
        exec(code, dsl_env)
    except Exception as e:
        error_msg = traceback.format_exc()
        return error_msg
    
    pred_grid = dsl_env.get('O', None)
    if pred_grid is None:
        return 'Output grid not found'
    if output_grid is not None and pred_grid != output_grid:
        return 'Output grid differs from input grid'
    
    return 'Ok'

if __name__ == '__main__':
    task = read_task('4c4377d9', 'training')
    solve_4c4377d9 = """x1 = hmirror(I)
O = vconcat(x1, I)"""

    print(verify_dsl_code(solve_4c4377d9, task['train'][0]['input'], task['train'][0]['output']))

    # a61ba2ce