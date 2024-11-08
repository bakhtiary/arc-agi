import base64
import io

import matplotlib.axes
import numpy as np
import matplotlib
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

def single_grid_to_base64(grid, draw_edges=True, draw_spine_border=False) -> str:
    fig, ax = plt.subplots()
    draw_single_axis(ax, grid, draw_edges=draw_edges, draw_spine_border=draw_spine_border)
    result = current_figure_to_base64()
    plt.close(fig)
    return result

def grids_all_in_one_to_base64(all_pairs, draw_edges=True, draw_spine_border=False) -> str:
    fig, axs = plt.subplots(len(all_pairs), 2, figsize=(10, 5*len(all_pairs)))
    for i, sample in enumerate(all_pairs):
        draw_single_axis(axs[i, 0], sample['input'], draw_edges=draw_edges, draw_spine_border=draw_spine_border)
        draw_single_axis(axs[i, 1], sample['output'], draw_edges=draw_edges, draw_spine_border=draw_spine_border)

    result = current_figure_to_base64()
    plt.close(fig)
    return result

def current_figure_to_base64():
    bytes_io = io.BytesIO()
    plt.savefig(bytes_io, format='jpg', bbox_inches='tight')
    bytes_io.seek(0)
    base64_data = base64.b64encode(bytes_io.read()).decode()
    return base64_data    

def draw_single_axis(ax: matplotlib.axes.Axes, grid, draw_edges=True, draw_spine_border=False):
    draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)
    # if draw_edges:
    #     draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)
    # else:
    #     draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)

def draw_single_axis_pcolormesh(ax: matplotlib.axes.Axes, grid, draw_edges=True, draw_spine_border=False):
    if draw_edges:
        linewidth = 10 - ((max(len(grid), len(grid[0]))-1)//10)*4
    else:
        linewidth = 0
    ax.pcolormesh(grid, cmap=arc_cmap, vmin=0, vmax=10, edgecolors='white', linewidth=linewidth)
    ax.invert_yaxis()
    ax.set_aspect('equal', adjustable='box')
    
    if not draw_spine_border:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    else:
        yticks = ax.get_yticks()
        yticklabels = ax.get_yticklabels()
        ax.set_yticks(yticks, reversed(yticklabels))
  