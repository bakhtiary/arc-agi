import sys
from solver import grid_list2tuple, grid_tuple2list
from task_utils import read_task

sys.path.append('arc-dsl')

from dsl import *
from arc_types import *
from constants import *

def solve_ff28f65a(I):
    x1 = objects(I, T, F, T)
    x2 = size(x1)
    x3 = double(x2)
    x4 = interval(ZERO, x3, TWO)
    x5 = apply(tojvec, x4)
    x6 = astuple(ONE, NINE)
    x7 = canvas(ZERO, x6)
    x8 = fill(x7, ONE, x5)
    x9 = hsplit(x8, THREE)
    O = merge(x9)
    return O


task = read_task('ff28f65a', 'training')
grid = task['train'][0]['input']
grid = grid_list2tuple(grid)
sol = grid_tuple2list(solve_ff28f65a(grid))
assert sol == task['train'][0]['output']
print('Test passed!')