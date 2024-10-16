import sys
from task_utils import read_task

sys.path.append('arga')

from image import Image

task = read_task('a64e4611', 'training')
grid = task['train'][0]['input']
a = Image('a64e4611', grid)
g = a.get_non_black_components_graph()
print(g.graph.nodes)
b = a