import datetime
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

class FuncsListResponse(BaseModel):
    thoughts: str
    func_list: list[str]


from llm_tool_writer_utils import extract_and_run_tool_code, extract_func_code_from_full_src, extract_func_name_from_signature, is_tool_writer_run_success
from llm_utils import HistoryManager, extract_code

DEFAULT_LLM = 'gpt-4o'
example_transformation_desc='''To analyze the transformations between the input and output grids, let's examine each pair of grids:

### Pair 1:
- **Input Grid (9x11):** Contains two shapes: a square with a hole (left) and a plus sign (right).
- **Output Grid:** The square with a hole is light blue, and the plus sign remains dark blue.
- **Transformation:** The square with a hole changes color from dark blue to light blue, while the plus sign remains unchanged.

### Pair 2:
- **Input Grid (12x11):** Contains a rotated square with a hole (left) and a rotated plus sign (right).
- **Output Grid:** The rotated square with a hole changes to light blue, while the rotated plus sign remains dark blue.
- **Transformation:** Similar to Pair 1, the square with a hole changes color, while the plus sign remains unchanged.

### Pair 3:
- **Input Grid (12x13):** Contains multiple shapes, including squares with holes and plus signs.
- **Output Grid:** All squares with holes change to light blue, while plus signs remain dark blue.
- **Transformation:** Consistent with previous pairs, squares with holes change color, while plus signs do not.

### Pair 4:
- **Input Grid (14x15):** Contains a mix of shapes, including squares with holes and plus signs.
- **Output Grid:** Squares with holes change to light blue, while plus signs remain dark blue.
- **Transformation:** The pattern is consistent across all pairs: squares with holes change color, while plus signs remain unchanged.

### General Observations:
- **Color Change:** Squares with holes change from dark blue to light blue.
- **No Change:** Plus signs remain dark blue.
- **Pattern Consistency:** The transformation is consistent across all grid sizes and configurations.

### Conclusion:
The transformation rule is to change the color of squares with holes to light blue, while leaving plus signs unchanged. This pattern is consistent across all examples provided.

If you need code to implement this mapping, please let me know!
'''

example_transformation_output = '''<FUNCTIONS>
detect_shapes(grid: List[List[int]]) -> List[List[Tuple[int, int, int]]]
identify_hole_in_shape(shape: List[Tuple[int, int, int]]) -> bool
change_color_of_shape(shape: List[Tuple[int, int, int]], new_color: int) -> List[Tuple[int, int, int]]'''



class LLMToolWriter:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.max_num_failed = 5
    
    def __call__(self, desc: str):
        if self.log_file:
            print(f'LLMToolWriter: Live view: http://localhost:5000/any_md?md_file={self.log_file}')
        else:
            print(f'LLMToolWriter: Live view not available. Pass `log_file` to `__init__`')

        results = {}
        func_signatures = self.get_tools_summaries(desc, num_beams=1)
        for func_signature in func_signatures:            
            func_name = extract_func_name_from_signature(func_signature)
            print(f'Getting code for {func_name}: {func_signature}')
            func_code = self.get_tool_with_tests(func_name, func_signature)
            if func_code:
                func_code_ = extract_func_code_from_full_src(func_name, func_code)
                results[func_name] = {'signature': func_signature, 'code': func_code_}
        return results

    def get_tools_summaries(self, desc: str, num_beams=3) -> list[str]:
        func_lists = []
        for i in range(num_beams):
            print(f'get_tools_summaries_one_beam ({i+1})')
            func_list = self.get_tools_summaries_one_beam(desc)
            print('\n'.join(func_list))
            if func_list:
                func_lists.append(func_list)
        
        tries_str = ''
        print('Getting summaries')
        for i, func_list in enumerate(func_lists, 1):
            tries_str += f'Try {i}:\n' + ('\n'.join(func_list)) + '\n\n'

        final_prompt = f'''I have asked an LLM several times to come up with a list of functions
that are useful for solving a task (task not shown here). Based on multiple attempts, give me a final
list of functions that seem most helpful in solving the task.


{tries_str}


Note: Please take your time to think. Then print <FUNCTIONS>, then give me a list of your chosen functions
keeping the annotations, and  placing each function on its own line.'''
        
        history_manager = HistoryManager(self.log_file)
        history_manager.add_singletone_text_message('system',
            'You are an intelligent assistant and a Python expert.', '|any-llm|')
            
        history_manager.add_singletone_text_message('user', final_prompt, DEFAULT_LLM)
        func_list_final = history_manager.chat_with_llm(DEFAULT_LLM, FuncsListResponse)
        if func_list_final:
            print('\n'.join(func_list_final.func_list))
            return func_list_final.func_list
        
        for func_list in func_lists:
            if func_list:
                return func_list
            
        return []
        
        # for num_failed in range(self.max_num_failed):
        #     assistant_reply = history_manager.chat_with_llm(DEFAULT_LLM)
        #     history_manager.add_singletone_text_message('assistant', resp, DEFAULT_LLM)
        #     if '<FUNCTIONS>' not in resp:
        #         history_manager.add_singletone_text_message('user',
        #             '<FUNCTIONS> not found in your response. Please send your response with the correct format.', DEFAULT_LLM)                
        #         num_failed += 1
        #     else:
        #         funcs = resp.split('<FUNCTIONS>')[1].splitlines()
        #         break
        # return funcs

    def get_tools_summaries_one_beam(self, desc: str, shots=0):
        prompt_0_shot = f''' # Task description
You need to extract useful tools (Python functions) that are helpful in composing a program that
implements the grid transformation described below. The following is a description of how an input
grid is transformed to an output grid. An LLM like you wants to write a Python function that implements
 the transformation. Your task is to extract and identify the nuts and bolts of this task.
 I will then ask you to write these as actual Python functions. Please take your time to think and then
 give me a list of subtask functions with clear names and type annotations.

# The grid transformation described for you
{desc}

# Notes:
- Print you final output after <FUNCTIONS> string, then give me a list of subtask functions with 
 clear names and type annotations, one function at a line
- Please give only relevant and concrete functions. Don't suggest vague or too general functions such as `parse_grid`, `solve_task`, `apply_transformation`, etc.
- Grids are represented as list of list of integers (colors) and objects as list of 3-tuples (x,y,color)
'''
        
        prompt_1_shot = f''' # Task description
You need to extract useful tools (Python functions) that are helpful in composing a program that
implements the grid transformation described below. The following is a description of how an input
grid is transformed to an output grid. An LLM like you wants to write a Python function that implements
 the transformation. Your task is to extract and identify the nuts and bolts of this task.
 I will then ask you to write these as actual Python functions. Please take your time to think.
 Then print <FUNCTIONS>, then give me a list of subtask functions with
 clear names and type annotations. Each line should contain the signature of only one function
 without any extra characters.

# Example:
## Description of the grid transformation
{example_transformation_desc}

## Sample output
{example_transformation_output}

# The grid transformation described for you
{desc}

# Notes:
- Print you final output after <FUNCTIONS> string, then give me a list of subtask functions with 
 clear names and type annotations, one function at a line
- Please give only relevant and concrete functions. Don't suggest vague or too general functions such as `parse_grid`, `solve_task`, `apply_transformation`, etc.
- Grids are represented as list of list of integers (colors) and objects as list of 3-tuples (x,y,color)
'''
        history_manager = HistoryManager(self.log_file)
        history_manager.add_singletone_text_message('system',
            'You are an intelligent assistant and a Python expert.', '|any-llm|')
            
        history_manager.add_singletone_text_message('user',
            prompt_0_shot if shots==0 else prompt_1_shot, DEFAULT_LLM)
        
        # Using structured outputs (https://github.com/BerriAI/litellm/issues/5074), not very helpful responces
        # 
        func_list = history_manager.chat_with_llm(DEFAULT_LLM, FuncsListResponse)
        if func_list:
            return func_list.func_list

    
    def get_tool_with_tests(self, func_name: str, func_signature: str) -> Callable:
        prompt = f'''You need to write a Python implemnetation of the following function in the context of
the a task that involve grids as list of lists of integers (colors). Please implement the function, and write useful tests using 
simple grids and/or shapes as needed, and enclose your codes in triple backticks code blocks. I will run the code block and in case of any error
or failing of the tests, will let you know the output.

{func_signature}

Note:
- Grids are represented as list of lists of ints.
- Intger values 0, 1, 2, ..., 9 represent different colors.
- The maximum size of grid is 30x30
- Shapes are represented as list of triples (x,y,color).
'''
        history_manager = HistoryManager(self.log_file)
        history_manager.add_singletone_text_message('system',
        'You are an intelligent assistant and a Python expert.', '|any-llm|')
        history_manager.add_singletone_text_message('user', prompt, DEFAULT_LLM)
        
        num_failed = 0
        while num_failed < self.max_num_failed:
            assistant_reply = history_manager.chat_with_llm(DEFAULT_LLM)
            history_manager.add_singletone_text_message('assistant', assistant_reply, DEFAULT_LLM)
            
            if f'def {func_name}' not in assistant_reply:
                history_manager.add_singletone_text_message('user',
                        f'Python function {func_name} not found in your response. Please correct your response.', DEFAULT_LLM)
                num_failed += 1
                continue
                
            run_results = extract_and_run_tool_code(assistant_reply)            
            with history_manager.start_new_message('user', DEFAULT_LLM):
                for obj in run_results:
                    history_manager.add_text(obj['text'])

            if is_tool_writer_run_success(run_results):
                return extract_func_code_from_full_src(func_name, assistant_reply)
            else:
                num_failed += 1
        
        return None
    