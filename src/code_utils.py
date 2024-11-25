import json
from pathlib import Path
import subprocess
from pathlib import Path
import ast

def ignore_for_llm_tools_docs(func):
    return func

# I added this because, there were function I didn't want to ignore, but leaving them as they were, made them include.
#   I added this so that we have more motivation to be explicit
def llm_tool(func):
    return func

def llm_action_tool(func):
    return func

def llm_lense_tool(func):
    return func

def run_any_code_read_outputs_with_timeout(args: list[str], code: bytes, timeout_seconds: int,
                                       python_file) -> list[dict]:
    proc = subprocess.Popen(['python', python_file] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # TODO: We could have also openned pipes streams in text mode by passing text=True and then code would be a str
    try:
        outs, errs = proc.communicate(input=code, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        return []
    
    jsonls = outs.decode()
    results = []
    
    for jsonl in jsonls.splitlines():
        if jsonl.strip() == '':
            continue
        try: # handle possible unstructured output from solve_fn 
            results.append(json.loads(jsonl.strip()))
        except json.JSONDecodeError as e:
            if not hasattr(e, 'ak_data'):
                e.ak_data = {}
            e.ak_data['state_machine_solver_utils'] = {
                'exception': e,
                'jsonls': jsonls
            }

    return results


def keep_only_defs_and_imports(code: str):
    try:
        parsed = ast.parse(code)
    except:
        return None
    to_keep_list = [node for node in parsed.body if isinstance(node, ast.FunctionDef)
        or isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
    to_keep_src = ''
    for to_keep in to_keep_list:
        to_keep_src += ast.unparse(to_keep) + '\n\n'
    return to_keep_src

def generate_tools_docs_by_ast(input_file, tool_type):
    file_content = Path(input_file).read_text()
    parsed = ast.parse(file_content)

    types_and_constants = []
    funcs = []

    tool_type_annotations = ['llm_tool']
    if tool_type in ['any', 'all']:
        tool_type_annotations.extend(['llm_action_tool', 'llm_lense_tool'])
    elif tool_type == 'action':
        tool_type_annotations.extend(['llm_action_tool'])
    elif tool_type == 'lense':
        tool_type_annotations.extend(['llm_lense_tool'])
    else:
        raise ValueError(f'{tool_type=} not supported.')

    # Collect names of functions to ignore
    functions_to_ignore, functions_to_include = set(), set()

    # First pass: find functions to ignore
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    if decorator.id == 'ignore_for_llm_tools_docs':
                        functions_to_ignore.add(node.name)
                    elif decorator.id in tool_type_annotations:
                        functions_to_include.add(node.name)

    # Second pass: extract functions, types, and constants
    for node in parsed.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            # Handle type definitions and constants
            if isinstance(node, ast.Assign):
                # For assignments like BLUE = 1
                targets = [t.id for t in node.targets if isinstance(t, ast.Name) if not t.id.endswith('_')]
                value = ast.get_source_segment(file_content, node.value).strip()
                for target in targets:
                    types_and_constants.append(f"{target} = {value}")
            elif isinstance(node, ast.AnnAssign):
                # For annotated assignments like Grid: List[int] = []
                target = node.target.id if isinstance(node.target, ast.Name) else ''
                annotation = ast.get_source_segment(file_content, node.annotation).strip()
                if not target.endswith('_'):
                    if node.value:
                        value = ast.get_source_segment(file_content, node.value).strip()
                        types_and_constants.append(f"{target}: {annotation} = {value}")
                    else:
                        types_and_constants.append(f"{target}: {annotation}")
        elif (isinstance(node, ast.FunctionDef) and node.name in functions_to_include and
              node.name not in functions_to_ignore and not node.name.endswith('_')):
            # Extract function details
            func_name = node.name
            args = []
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    annotation = ast.get_source_segment(file_content, arg.annotation).strip()
                    arg_str += f": {annotation}"
                args.append(arg_str)
            # Handle *args and **kwargs
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")
            returns = "None"
            if node.returns:
                returns = ast.get_source_segment(file_content, node.returns).strip()
            docstring = ast.get_docstring(node) or ''
            func_signature = f"def {func_name}({', '.join(args)}) -> {returns}:"
            if docstring:
                func_doc = f'    """{docstring}"""'
                funcs.append(f"{func_signature}\n{func_doc}\n")
            else:
                funcs.append(f"{func_signature}\n")

    types_and_constants_str = '\n'.join(types_and_constants)
    funcs_str = '\n'.join(funcs)

    return f'Types and Constants:\n{types_and_constants_str}\n\nFunctions:\n{funcs_str}'
