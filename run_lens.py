from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from dataset import LocalDataset
from image_utils import single_grid_to_base64
from lens_orthogonal import desc_to_nested_str, describe_objects_orthogonal_hierarchy
from tools_src_mini import get_grid_objects_hierarchy


LOG_DIR = Path('logs-etc') / 'lens' / 'orthogonal' / datetime.now().strftime('%Y%m%d-%H%M%S')

def grid_to_lens_html(grid):
    result = f'<div><img src="data:image/jpeg;base64,{single_grid_to_base64(grid, draw_edges=False, draw_spine_border=True)}"></div>'
    objs = get_grid_objects_hierarchy(grid, univalued=True)
    descs = describe_objects_orthogonal_hierarchy(objs, univalued=True)
    return result + '<pre>' + '\n'.join(desc_to_nested_str(desc) for desc in descs) + '</pre>'

if __name__ == '__main__':
    hard_ids = ['beb8660c', '72ca375d', '82819916', 'b2862040', '846bdb03', '855e0971', '05269061', '72322fa7', 
        '56dc2b01', '6d75e8bb']
    average_ids = ['91714a58', '50cb2852', 'a61f2674', '85c4e7cd', 'd0f5fe59', '49d1d64f', 'b60334d2', 'd511f180', 
        'e98196ab', '56ff96f3']
    task_ids = hard_ids + average_ids

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print(f'Saving to file://wsl.localhost/Ubuntu/{LOG_DIR.absolute()}')
    for task_id in tqdm(task_ids):
        print(f'Processing {task_id} ...')       
        task = LocalDataset('training').read_task(task_id)
        html_content = ''
        for i,sample in enumerate(task["train"], 1):
            html_content += f'<h3>Train pair {i}</h3>'
            html_content += grid_to_lens_html(sample['input'])
            html_content += grid_to_lens_html(sample['output'])
            html_content += '<hr>'                

        for i,sample in enumerate(task["test"], 1):
            html_content += f'<h3>Test pair {i}</h3>'
            html_content += grid_to_lens_html(sample['input'])

        (LOG_DIR / f'{task_id}.html').write_text(html_content)
