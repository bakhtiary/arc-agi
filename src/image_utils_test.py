from matplotlib import pyplot as plt

from dataset import LocalDataset
from image_utils import draw_single_axis


fig, ax = plt.subplots()
I = LocalDataset('training').read_task('beb8660c')['train'][0]['input']
draw_single_axis(ax, I, draw_edges=False, draw_spine_border=True)
plt.savefig('image_utils_test_1.png', bbox_inches='tight')