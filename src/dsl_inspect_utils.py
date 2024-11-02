from pathlib import Path
import re
import importlib
import inspect
import dis
import sys

print('Adding arc-dsl to sys.path ...')
sys.path.append('arc-dsl')

def generate_dsl_docs_inspect_dict():
    docs_str = []
    docs_dict = generate_dsl_docs_inspect_dict()
    for func_name, doc_dict in docs_dict.items():
        docs_str.append(f"def {func_name}({', '.join(doc_dict['params'])}) -> {doc_dict['return']}:  # {doc_dict['doc']}")
    return '\n'.join(docs_str)

def generate_dsl_docs_inspect_dict():
    dsl_module = importlib.import_module('dsl')
    functions = inspect.getmembers(dsl_module, inspect.isfunction)
    docs_dicts = {}
    for name, func in functions:
        sig = inspect.signature(func)
        annotations = func.__annotations__
        params = []
        for param_name, param in sig.parameters.items():
            if param_name in annotations:
                param_type = annotations[param_name]
                params.append(f"{param_name}: {param_type}")
            else:
                params.append(f"{param_name}: {param.annotation if param.annotation is not inspect.Parameter.empty else 'Any'}")
        
        return_type = annotations.get('return', 'None')
        doc = inspect.getdoc(func)
        doc_short = doc.split('.')[0] if doc else 'No description available'
        docs_dicts[name] = {'params': params,
            'return': return_type.__name__ if isinstance(return_type, type) else return_type,
            'doc': doc_short
        }
    
    return docs_dicts


def generate_dsl_docs_parse():
    file_content = (Path('arc-dsl') / 'dsl.py').read_text()
    function_pattern = re.compile(
        r"(def\s+\w+\(.*?\)\s*->\s*[^\:]*:\s*\"\"\"[^\"]*\"\"\"\n)(?:.|\n)*?(?=\ndef|\Z)", 
        re.DOTALL
    )

    def format_function(match):
        function_signature_and_doc = match.group(1)
        function_signature_and_doc = re.sub(r"\s*\n\s*", " ", function_signature_and_doc)
        function_signature_and_doc = function_signature_and_doc.replace(': """', '  #')
        function_signature_and_doc = function_signature_and_doc.replace('"""', '')
        return function_signature_and_doc
    
    types = (Path('arc-dsl') / 'arc_types.py').read_text().strip()
    
    funcs = function_pattern.sub(format_function, file_content)
    funcs = '\n'.join([f.strip() for f in funcs.splitlines()[3:]])

    return f'Types:\n{types}\n\n\nFunctions:\n{funcs}'


def get_solution_docs(task_id):
    solvers_module = importlib.import_module('solvers')
    func = solvers_module.__dict__.get(f'solve_{task_id}', None)
    if func is None:
        return None
    
    docs_dict = generate_dsl_docs_inspect_dict()
    bytecode = dis.get_instructions(func)
    called_functions = []
    docs_str = []
    for instruction in bytecode:
        if instruction.opname == 'CALL_FUNCTION':
            func_name = called_functions.append(instruction.argval)
            docs_str.append(docs_dict[func_name])
            
    return '\n'.join(docs_str)


if __name__ == '__main__':
    # tool_docs_parse = generate_dsl_docs_parse()
    # print(tool_docs_parse)

    get_solution_docs('ff28f65a')
