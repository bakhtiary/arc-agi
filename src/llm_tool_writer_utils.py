from pathlib import Path
import re
from typing import Callable
from code_utils import run_any_code_read_outputs_with_timeout
from llm_utils import extract_code

current_file_directory = Path(__file__).parent

def tool_to_single_doc(funcs: list[Callable]):
    return [func.__name__ for func in funcs]

def extract_and_run_tool_code(response):
    code = extract_code(response)
    if code is None:
        return '''Code block not found in your response. Please ensure you enclose your functions in triple backticks.'''
    return run_any_code_read_outputs_with_timeout([], code.encode(), 20, current_file_directory/'tool_writer_code_runner.py')


def is_tool_writer_run_success(run_results):
    return (
        len(run_results) >= 1 and
        'text' in run_results[-1] and
        run_results[-1]['text'] == '|successful run|'
    )

def extract_func_name_from_signature(signature: str) -> str:
    # Regex to match optional def, * def, - def, or nothing, and capture function name
    match = re.search(r'[-*]?\s*(?:def\s+)?(\w+)\s*\(', signature)
    if match:
        return match.group(1)
    return None

def extract_func_code_from_full_src(func_name: str, full_src: str):
    # TODO: improve
    return full_src