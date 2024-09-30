# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

from task_utils import get_tasks
from solver import beam_solve
from experimenter import experiment


LOG_DIR = Path('log') / datetime.now().strftime('%Y%m%d-%H%M%S')

def crappy_solve(task_id, dataset, num_beams, log_dir):
    print('crap')
    return log_dir, dataset, task_id, []

if __name__ == "__main__":
    dataset = 'training'
    # task_ids = ["c8f0f002"]
    # md analysis by amir --> ff28f65a
    task_ids = get_tasks(dataset)[0:10]
    experiment(beam_solve, task_ids, LOG_DIR, dataset=dataset, pool_size=10)


