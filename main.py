# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

import os
from datetime import datetime
from pathlib import Path

from solver import beam_solve
from experimenter import experiment

LOG_DIR = Path('log') / datetime.now().strftime('%Y%m%d-%H%M%S')


if __name__ == "__main__":
    training_dir = "data/training"
    task_ids = [f.split(".")[0] for f in os.listdir(training_dir)] [4:8]
    experiment(beam_solve, task_ids, LOG_DIR, dataset="training")
