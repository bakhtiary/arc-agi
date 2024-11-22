import numpy as np


AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]


def grid_list2tuple(grid: AKGrid) -> AKGridTuple:
    return tuple(tuple(row) for row in grid)


def grid_tuple2list(grid: AKGridTuple) -> AKGrid:
    return list(list(row) for row in grid)


def grid_is_correct(pred_grid):
    # This alone does not handle None in the arrays
    try:
        t = np.array(pred_grid)
        if len(t.shape) != 2:
            return False
    except:
        return False
    
    for elem in pred_grid:
        if not all(isinstance(x, int) for x in elem):
            return False
    
    return True
    
def join_with_and(items):
    if not items:
        return ''
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return items[0] + ' and ' + items[1]
    else:
        return ', '.join(items[:-1]) + ', and ' + items[-1]


def get_grid_sizes(task, which) -> str:
    input_sizes_train = [(len(pair['input']), len(pair['input'][0])) for pair in task['train']]
    output_sizes_train = [(len(pair['output']), len(pair['output'][0])) for pair in task['train']]
    input_sizes_test = [(len(pair['input']), len(pair['input'][0])) for pair in task['test']]

    result = ''
    if len(set(input_sizes_train)) == 1:  # for both cases where which = 'all' or a pair index
        m,n = input_sizes_train[0]
        result += f'All input sizes are the same {m}x{n}'
        if input_sizes_test[0] != (m,n):
            result += f' for the displayed images. However, it could be somethings else, such as: ' + ' or '.join(f'{m}x{n}' for m,n in set(input_sizes_test)) + '.'
        else:
            result += '.'
    elif which == 'all':
        result += f'Sizes of displayed input images are ' + join_with_and([f'{m}x{n}' for m,n in input_sizes_train]) + '.'
    else: # which is a pair index, such as 0
        m,n = input_sizes_train[which]
        result += f'The size of the displayed input image is {m}x{n}.'
        other_sizes = set(input_sizes_train + input_sizes_test) - {(m,n)}
        result += (f' However, it could be somethings else, such as: ' +
                    ' or '.join([f'{m}x{n}' for m,n in other_sizes]) + '.')
            

    if all(x == y for x,y in zip(input_sizes_train, output_sizes_train)):
        result += ' Output image size is always the same as the input.'
    elif len(set(output_sizes_train)) == 1: # for both cases where which = 'all' or a pair index
        a_size = output_sizes_train[0]
        result += f' All output sizes are the same {a_size[0]}x{a_size[1]}.'            
    elif which == 'all':
        result += f' Sizes of displayed ouput images are ' + join_with_and([f'{m}x{n}' for m,n in output_sizes_train]) + '.'
    else: # which is a pair index, such as 0
        m,n = output_sizes_train[which]
        result += f' The size of the displayed input image is {m}x{n}.'
        other_sizes = set(output_sizes_train) - {(m,n)}
        result += (f' However, it could be somethings else, such as: ' +
                    ' or '.join(f'{m}x{n}' for m,n in other_sizes) + '.')

    return result