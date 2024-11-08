from pathlib import Path
import sys

from dataset import LocalDataset
from grid_utils import grid_list2tuple

sys.path.append(str(Path(__file__).parent / 'arc_dsl'))
from arc_dsl.solvers import *

I = LocalDataset('training').read_task('beb8660c')['train'][0]['input']
It = grid_list2tuple(I)
print(solve_beb8660c(It))