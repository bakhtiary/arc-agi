# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

import os
from datetime import datetime
from idlelib.run import flush_stdout
from multiprocessing import Pool
from pathlib import Path

from solver import beam_solve
from experimenter import experiment

LOG_DIR = Path('log') / datetime.now().strftime('%Y%m%d-%H%M%S')

def crappy_solve(task_id, dataset, num_beams, log_dir):
    return log_dir, dataset, task_id, []

if __name__ == "__main__":
    training_dir = "data/training"
    task_ids = [f.split(".")[0] for f in os.listdir(training_dir)] [4:8]
    experiment(crappy_solve, task_ids, LOG_DIR, dataset="training")


