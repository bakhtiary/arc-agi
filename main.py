# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

from datetime import datetime
from pathlib import Path
import warnings

import litellm

from simple_lens_state_machine import SimpleLensStateMachine
from state_machine_solver import StateMachineSolver
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

from experimenter import experiment

load_dotenv(".secrets")

LOG_DIR = Path('logs') / datetime.now().strftime('%Y%m%d-%H%M%S')

def crappy_solve(task_id, dataset, num_beams, log_dir):
    print('crap')
    return task_id, dataset, log_dir, []

if __name__ == "__main__":
    dataset = 'training'
    task_ids = ["c8f0f002"]
    # md analysis by amir --> ff28f65a
    # task_ids = get_tasks(dataset)[0:10]
    # task_ids = get_task_mix('training', simple=10, hard=10)

    state_machine_solver = StateMachineSolver(SimpleLensStateMachine, litellm)
    
    experiment(state_machine_solver, task_ids, dataset, LOG_DIR, pool_size=-1)


