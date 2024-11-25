import base64
import io

import matplotlib.axes
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image

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

def pil_image_to_base64(image: Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_pil_image(base64_str: str) -> Image:
    buffered = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(buffered), formats=["PNG"])

def single_grid_to_base64(grid, draw_edges=True, draw_spine_border=False) -> str:
    fig, ax = plt.subplots()
    draw_single_axis(ax, grid, draw_edges=draw_edges, draw_spine_border=draw_spine_border)
    result = current_figure_to_base64()
    plt.close(fig)
    return result

def grids_all_in_one_to_base64(all_pairs: list[dict], draw_edges=True, draw_spine_border=False) -> str:
    fig, axs = plt.subplots(len(all_pairs), 2, figsize=(10, 5*len(all_pairs)))
    for i, sample in enumerate(all_pairs):
        draw_single_axis(axs[i, 0], sample['input'], draw_edges=draw_edges, draw_spine_border=draw_spine_border)
        draw_single_axis(axs[i, 1], sample['output'], draw_edges=draw_edges, draw_spine_border=draw_spine_border)

    result = current_figure_to_base64()
    plt.close(fig)
    return result

def current_figure_to_base64():
    bytes_io = io.BytesIO()
    plt.savefig(bytes_io, format='png', bbox_inches='tight')
    bytes_io.seek(0)
    base64_data = base64.b64encode(bytes_io.read()).decode()
    return base64_data    

def draw_single_axis(ax: matplotlib.axes.Axes, grid, draw_edges=True, draw_spine_border=False):
    draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)
    # if draw_edges:
    #     draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)
    # else:
    #     draw_single_axis_pcolormesh(ax, grid, draw_edges, draw_spine_border)

def integerize_labels(ticks: list[float], labels: list[str]) -> list[str]:
    return ticks, labels
    new_ticks, new_labels = [], []
    for tick, label in zip(ticks, labels):
        if tick == int(tick):
            new_ticks.append(tick)
            new_labels.append(str(int(tick)))
        else:
            new_ticks.append(tick)
            new_labels.append('')
    return new_ticks, new_labels


def draw_single_axis_pcolormesh(ax: matplotlib.axes.Axes, grid, draw_edges=True, draw_spine_border=False):
    if draw_edges:
        linewidth = 10 - ((max(len(grid), len(grid[0]))-1)//10)*4
    else:
        linewidth = 0
    ax.pcolormesh(grid, cmap=arc_cmap, vmin=0, vmax=10, edgecolors='white', linewidth=linewidth)
    
    # Note: In pcolormesh function, "the column index corresponds to the x-coordinate,
    # and the row index corresponds to y". https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.pcolormesh.html
    # Therefore, grid is indexed as grid[y][x]. That is, "The grid orientation follows the standard matrix
    # convention: An array C with shape (nrows, ncolumns) is plotted with the column number as X and
    # the row number as Y." This is in line with arc, with the only difference that, in ARC, officially,
    # grids are depicted with inverted y, that is from top to bottom, for example,
    # the grid [[7, 0, 7], [7, 0, 7], [7, 7, 0]] (task 007bbfb7) is depicted as
    #   7 0 7
    #   7 0 7
    #   7 7 0
    # (see https://arcprize.org/play?task=007bbfb7)
    # This is the same way that LLM understand lists of lists (... When you provide a grid as a list of lists ... to me,
    # I typically interpret it from top to bottom ... (chat with o1-preview)). Therefore, we use the following line
    # to invert the grid (equivalent to `imshow`'s `origin='upper'``):
    ax.invert_yaxis()
    
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(0,len(grid[0]))
    if not draw_spine_border:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    else:
        # print(integerize_labels(ax.get_xticks(), ax.get_xticklabels()))
        #ax.set_xticks(*integerize_labels(ax.get_xticks(), ax.get_xticklabels()))
        xticks = range(0,len(grid[0]),max(1, len(grid[0])//6))
        ax.set_xticks(xticks, map(str, xticks))
        ax.xaxis.set_ticks_position('top')  # Move ticks to the top
        ax.xaxis.set_label_position('top')
        # reverse needed for official depiction (see above)
        #ax.set_yticks(*integerize_labels(ax.get_yticks(), ax.get_yticklabels()))
        yticks = range(0,len(grid),max(1, len(grid)//6))
        ax.set_yticks(yticks, map(str, yticks))

  