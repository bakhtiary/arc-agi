import base64
import io

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from task_utils import get_tasks
from dataset import LocalDataset

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

def single_grid_to_base64(grid, draw_edges=True, hide_spine_border=True) -> str:
    fig, ax = plt.subplots()
    draw_single_axis(ax, grid, draw_edges=draw_edges, hide_spine_border=hide_spine_border)
    result = current_figure_to_base64()
    plt.close(fig)
    return result

def grids_all_in_one_to_base64(all_pairs, draw_edges=True, hide_spine_border=True) -> str:
    fig, axs = plt.subplots(len(all_pairs), 2, figsize=(10, 5*len(all_pairs)))
    for i, sample in enumerate(all_pairs):
        draw_single_axis(axs[i, 0], sample['input'], draw_edges=draw_edges, hide_spine_border=hide_spine_border)
        draw_single_axis(axs[i, 1], sample['output'], draw_edges=draw_edges, hide_spine_border=hide_spine_border)

    result = current_figure_to_base64()
    plt.close(fig)
    return result

def current_figure_to_base64():
    bytes_io = io.BytesIO()
    plt.savefig(bytes_io, format='jpg')
    bytes_io.seek(0)
    base64_data = base64.b64encode(bytes_io.read()).decode()
    return base64_data    

def draw_single_axis(axis_0, sample_grid, draw_edges=True, hide_spine_border=True):
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