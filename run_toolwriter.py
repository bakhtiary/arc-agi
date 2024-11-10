from datetime import datetime
from pathlib import Path

import sys
import warnings

from dataset import LocalDataset
from llm_tool_writer_utils import extract_func_name_from_signature
from llm_utils import HistoryManager, LLMInterface, LiteLLMInterface, chat_with_llm
from simple_state_machine_distinct_pairs_with_tools import SimpleStateMachineDistinctPairswithTools
from state_machine_solver import StateMachineSolver
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

from dotenv import load_dotenv

import llm_tool_writer
from llm_tool_writer import DEFAULT_LLM, LLMToolWriter

load_dotenv(".secrets")

current_file_directory = Path(__file__).parent
LOG_DIR = Path('logs-etc') / 'toolwriter' / datetime.now().strftime('%Y%m%d-%H%M%S')

class TeeForOutput:
    def __init__(self, files):
        self.files = files

    def write(self, text):
        for file in self.files:
            file.write(text)

if __name__ == "__main__":
    log_file = LOG_DIR / '1.md'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    task_id = t_order_bars_by_color = 'beb8660c'
    dataset = LocalDataset('training')
    
    history_manager = HistoryManager(log_file)
    state_machine = SimpleStateMachineDistinctPairswithTools(task_id, dataset)
    cur_state = state_machine.states['entry_point']
    llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='gpt-4o')
    state_machine_solver = StateMachineSolver(SimpleStateMachineDistinctPairswithTools, llm_interface)
    state_machine_solver.add_state_machine_messages(cur_state['message_to_send'],
        DEFAULT_LLM, history_manager)
    
    hypothesis = chat_with_llm(llm_interface, history_manager, LLMInterface.TEXT_ADVANCED) 
    
    llm_tool_writer_ = LLMToolWriter(llm_interface, log_file=log_file)
    funcs = llm_tool_writer_.get_tools_summaries(hypothesis, num_beams=1)
    print('\n'.join(funcs))

    # func_name = extract_func_name_from_signature(funcs[0])
    # llm_tool_writer_.get_tool_with_tests(func_name, funcs[0])
