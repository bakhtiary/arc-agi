from datetime import datetime
from pathlib import Path

import sys
import warnings

from llm_tool_writer_utils import extract_func_name_from_signature
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

from dotenv import load_dotenv

import llm_tool_writer
from llm_tool_writer import LLMToolWriter

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
    llm_tool_writer_ = LLMToolWriter(log_file=log_file)
    funcs = llm_tool_writer_.get_tools_summaries(llm_tool_writer.example_transformation_desc, num_beams=1)
    print('\n'.join(funcs))

    func_name = extract_func_name_from_signature(funcs[0])
    llm_tool_writer_.get_tool_with_tests(func_name, funcs[0])


