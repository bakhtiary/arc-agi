import numpy as np


AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]


def grid_list2tuple(grid: AKGrid) -> AKGridTuple:
    return tuple(tuple(row) for row in grid)


def grid_tuple2list(grid: AKGridTuple) -> AKGrid:
    return list(list(row) for row in grid)


def grid_is_correct(pred_grid):
    try:
        t = np.array(pred_grid)
        return len(t.shape) == 2
    except:
        return False