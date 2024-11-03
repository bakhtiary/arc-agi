import base64
import io

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from task_utils import get_tasks, Dataset

ARC_COLORS = [
    '#000',
    '#0074D9',  # /* blue */
    '#FF4136',  # /* red */
    '#2ECC40',  # /* green */
    '#FFDC00',  # /* yellow */
    '#AAAAAA',  # /* grey */
    '#F012BE',  # /* fuschia */
    '#FF851B',  # /* orange */
    '#7FDBFF',  # /* teal */
    '#870C25',  # /* brown */
]
arc_cmap = ListedColormap(ARC_COLORS)


def make_image_base64(grid) -> str:
    plot_Image(grid)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData


def make_all_in_one_images_base64(all_grids, draw_edges=True, hide_spine_border=True) -> str:
    plot_all_in_one_images(all_grids)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData


def plot_Image(grid, draw_edges=True, hide_spine_border=True):
    fig, ax = plt.subplots()
    draw_axis(ax, grid, draw_edges=draw_edges, hide_spine_border=hide_spine_border)
    

def plot_all_in_one_images(all_samples, draw_edges=True, hide_spine_border=True):
    fig, axs = plt.subplots(len(all_samples), 2, figsize=(10, 5*len(all_samples)))
    for i, sample in enumerate(all_samples):
        draw_axis(axs[i, 0], sample['input'], draw_edges=draw_edges, hide_spine_border=hide_spine_border)
        draw_axis(axs[i, 1], sample['output'], draw_edges=draw_edges, hide_spine_border=hide_spine_border)


def draw_axis(axis_0, sample_grid, draw_edges=True, hide_spine_border=True):
    if draw_edges:
        linewidth = 10 - ((max(len(sample_grid), len(sample_grid[0]))-1)//10)*4
    else:
        linewidth = 0
    #sample_grid = np.array(sample_grid).T
    #print('a', sample_grid)

    axis_0.pcolormesh(sample_grid, cmap=arc_cmap, vmin=0, vmax=10, edgecolors='white', linewidth=linewidth)
    axis_0.set_xticks([])
    axis_0.set_yticks([])
    axis_0.invert_yaxis()

    if hide_spine_border:
        for spine in axis_0.spines.values():
            spine.set_visible(False)

    axis_0.axis('equal')

def draw_all():
    task_ids = get_tasks('training')
    for task_id in task_ids:
        draw_specific_single(task_id)
        plt.show()

def draw_crap():
    sample_inputs = [{'input': [[1, 1, 1], [0, 0, 0], [0, 0, 0]], 'output': [[0, 0, 0], [1, 1, 1], [0, 0, 0]]},
                     {'input': [[0, 0, 0], [1, 1, 1], [0, 0, 0]], 'output': [[0, 0, 0], [0, 0, 0], [1, 1, 1]]},
                     {'input': [[0, 1, 0], [1, 1, 0], [0, 0, 0]], 'output': [[0, 0, 0], [0, 1, 0], [1, 1, 0]]},
                     {'input': [[0, 2, 2], [0, 0, 2], [0, 0, 0]], 'output': [[0, 0, 0], [0, 2, 2], [0, 0, 2]]}]
    plot_all_in_one_images(sample_inputs)
    plt.savefig('grid_visualization.png')
    plt.show()

def draw_specific_all(task_id, draw_id=True):
    train = Dataset("training").read_task(task_id )['train']
    plot_all_in_one_images(train)
    if draw_id:
        plt.figtext(0.5, 0.01, task_id, wrap=True, horizontalalignment='center', fontsize=12)
    plt.savefig('grid_visualization.png')
    plt.show()

def draw_specific_single(task_id, draw_id=True):
    train = Dataset('training').read_task(task_id)['train']
    plot_Image(train[0]['input'])
    if draw_id:
        plt.figtext(0.5, 0.01, task_id, wrap=True, horizontalalignment='center', fontsize=12)
    plt.savefig('grid_visualization.png')
    plt.show()

if __name__ == "__main__":
    # draw_crap()
    # draw_all()
    # tests for 30x30 images
    draw_specific_all('a64e4611', draw_id=False)
    # draw_specific_single('a64e4611')
    # draw_specific_all('ff28f65a', draw_id=False)
    
