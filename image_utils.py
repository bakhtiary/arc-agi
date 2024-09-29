import base64
import io

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from task_utils import get_tasks, read_task

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


def make_image_base64(input_grid):

    plt.imshow(input_grid, cmap=arc_cmap, vmin=0, vmax=10)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData


def make_all_images_base64(input_grid):
    plot_all_Images(input_grid)
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData


def plot_all_Images(all_samples):
    fig, axs = plt.subplots(len(all_samples),2,figsize=(10, 5*len(all_samples) ))
    for i, sample in enumerate(all_samples):
        draw_axis(axs[i, 0], sample['input'])
        draw_axis(axs[i, 1], sample['output'])


def draw_axis(axis_0, sample_grid):
    axis_0.imshow(sample_grid, cmap=arc_cmap, vmin=0, vmax=10)
    # axis_0.set_xticks(np.arange(0.5, axis_0.get_xlim()[1]-0.5, 1))
    # axis_0.set_yticks([0.5,1.5])
    # axis_0.grid()
    axis_0.tick_params(
        bottom=False,  # ticks along the bottom edge are off
        labelbottom=False,
        left=False,
        labelleft=False,
    )  # labels along the bottom edge are off
    # axis_0.axis("equal")

def draw_all():
    tasks = get_tasks("training")
    for task in tasks:

        plot_all_Images(read_task(task,dataset='training')['train'])
        plt.figtext(0.5, 0.01, task, wrap=True, horizontalalignment='center', fontsize=12)
        plt.show()

def draw_one():
    sample_inputs = [{'input': [[1, 1, 1], [0, 0, 0], [0, 0, 0]], 'output': [[0, 0, 0], [1, 1, 1], [0, 0, 0]]},
                     {'input': [[0, 0, 0], [1, 1, 1], [0, 0, 0]], 'output': [[0, 0, 0], [0, 0, 0], [1, 1, 1]]},
                     {'input': [[0, 1, 0], [1, 1, 0], [0, 0, 0]], 'output': [[0, 0, 0], [0, 1, 0], [1, 1, 0]]},
                     {'input': [[0, 2, 2], [0, 0, 2], [0, 0, 0]], 'output': [[0, 0, 0], [0, 2, 2], [0, 0, 2]]}]
    plot_all_Images(sample_inputs)
    plt.show()

def draw_specific(task_id="a64e4611"):
    plot_all_Images(read_task(task_id, dataset='training')['train'])
    plt.figtext(0.5, 0.01, task_id, wrap=True, horizontalalignment='center', fontsize=12)
    plt.show()



if __name__ == "__main__":
    draw_one()
    # draw_all()
    # draw_specific()
    

