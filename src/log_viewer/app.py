import os
from collections import defaultdict
import itertools
from pathlib import Path
import re


from flask import Flask, render_template, jsonify, request
from werkzeug.middleware.profiler import ProfilerMiddleware
import markdown

from calc_logs_statistics import get_log_summary_by_experiments, get_log_summary_by_tasks, task_summary_to_ladder
from dataset import LocalDataset
from image_utils import grids_all_in_one_to_base64, single_grid_to_base64
from state_machine_solver_utils import run_task_code_read_outputs_with_timeout
from tools_src_mini import get_grid_objects_as_flat_list, get_grid_objects_hierarchy
from lens_orthogonal import describe_objects_orthogonal_flat, describe_objects_orthogonal_hierarchy

current_file_dir = Path(__file__).parent
log_root_dirs = [Path('important-run-logs'), Path('logs')]

app = Flask(__name__)
# Uncomment for profiling
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=(str(current_file_dir.parent),))

def get_task_level(dataset, task_id):
    log_summary_task = get_log_summary_by_tasks(log_root_dirs)
    log_ladder = task_summary_to_ladder(log_summary_task)
    
    if task_id not in log_summary_task[dataset]:
        return 'n/a'
    
    sum_score = sum(score for root_dir, log_dir, score in log_summary_task[dataset][task_id])
    return f'{sum_score} / {len(log_summary_task[dataset][task_id])}'

def dictionary_order_iterator():
    length = 1
    while True:
        for chars in itertools.product('abcdefghijklmnopqrstuvwxyz', repeat=length):
            yield ''.join(chars)
        length += 1
        
@app.route('/task_summary')
def task_summary():
    log_summary_task = get_log_summary_by_tasks(log_root_dirs)
    log_ladder = task_summary_to_ladder(log_summary_task)
    html = '''
<style>
.task-id {
    font-family: Courier New;
}
.succ {
    background-color: lightgreen;
}
.fail {
}
.exp {
    background-color: #fffdd0;
    padding: 3px;
    margin: 3px;
    border-radius: 10px;
    display: inline-block;
}
</style>
'''
    all_log_ids = get_all_log_ids(log_root_dirs)
    iterator = dictionary_order_iterator()
    log_id_symbols = {all_log_id: next(iterator) for all_log_id in all_log_ids}

    log_summary_exp = get_log_summary_by_experiments(log_root_dirs)
    def tr_order(e):
        return ['not_in_results_json','success_ok', 'success_nok', 'error', 'timeout', 'n/a'].index(e[0])
    
    html += f'<h1>Task summary based on aggregate of <i>{log_root_dirs}</i></h1>'
    html += '<h2>Legend</h2>'
    html += '* after a task name ==> multiple md files (to see them got to the task page and select other md files)<br><br>'
    for (root_dir, log_id), rest in log_summary_exp.items():
        summary = ', '.join([f'{tr}: {len(task_ids)}' for tr, task_ids in sorted(rest.items(),key=tr_order)])
        html += f'<span class="exp">{log_id} ({summary}, {log_id_symbols[log_id]})</span>'
        
    html  += f'<hr>'
    for dataset, rest in log_ladder.items():
        html += f'<h2>Dataset: {dataset}</h2>'
        for sum_score, task_ids in rest.items():
            sum_dict = defaultdict(int)
            for task_id, log_ids in task_ids.items():
                for root_dir,log_id,score in sorted(log_ids):
                    if score != 0:
                        sum_dict[log_id] += 1

            summary = ', '.join(f'{log_id_symbols[log_id]}={v}' for log_id,v in sorted(sum_dict.items()))
            html += f'<h3>Score: {sum_score:.2f} ({len(task_ids)}: {summary})</h3>'
            
            for task_id, log_ids in task_ids.items():
                a_tags = []
                for root_dir, log_id, score in sorted(log_ids):
                    astrisc = '*' if len(list((Path(root_dir) / log_id / task_id).glob("*.full.md"))) > 1 else ''
                    a_class = 'succ' if score != 0 else 'fail'
                    a_tags.append(f'<a class="{a_class}" href="/#{root_dir.name}/{log_id}/{task_id}/1.full.md">{log_id_symbols[log_id]}{astrisc}</a>')
                a_tags_html = ', '.join(a_tags)
                html += f'<span class="task"><span class="task-id">{task_id}</span> ({a_tags_html})</span> '
        html += '<hr>'
    return html

@app.route('/experiment_summary')
def experiment_summary():
    html = '''
<style>

</style>
'''
  
    log_summary_exp = get_log_summary_by_experiments(log_root_dirs)
    def tr_order(e):
        return ['not_in_results_json', 'success_ok', 'success_nok', 'error', 'timeout', 'n/a'].index(e[0])
    
    html += f'<h1>Experiment summary based on aggregate of <i>{log_root_dirs}</i></h1>'
    html += '* after a task name ==> multiple md files (to see them got to the task page and select other md files)<br><br>'

    for (root_dir, log_id), rest in log_summary_exp.items():
        summary = 'total: ' + str(sum(len(task_ids) for tr, task_ids in rest.items())) + ': '
        summary += ', '.join([f'{tr}: {len(task_ids)}' for tr, task_ids in sorted(rest.items(),key=tr_order)])
        html += f'<h2 id="{root_dir}-{log_id}">{root_dir}/{log_id} ({summary})</h2>'
        
        notes = ''
        for a_root_dir in log_root_dirs:
            notes_file = a_root_dir / log_id / 'notes.txt'
            if notes_file.exists():
                notes += f'<div><b>Notes:</b> {notes_file.read_text()} (<i>{notes_file.relative_to(a_root_dir.parent)}</i>)</div>'

        html += notes
        for tr, task_ids in sorted(rest.items(),key=tr_order):
            if len(task_ids) == 0:
                continue
            html += f'<h3>{tr}</h3>'
            for task_id in task_ids:
                astrisc = '*' if len(list((Path(root_dir) / log_id / task_id).glob("*.full.md"))) > 1 else ''
                html += f'<a href="/#{root_dir}/{log_id}/{task_id}/1.full.md">{task_id} {astrisc}</a>&nbsp;&nbsp;'
        html += '<hr>'

    html += '''<script>const scrollTo = el => {
  if (el) {
    const top = window.scrollY + el.getBoundingClientRect().top
    window.scrollTo({ top: top, behavior: "smooth" })
  }
}

// wrap in a domReady type callback if needed
scrollTo(document.querySelector(window.location.hash))
</script>'''
    return html


def get_all_log_ids(log_root_dirs):
    all_log_ids = []
    for log_summary_root_dir in log_root_dirs:
        if log_summary_root_dir.exists():
            all_log_ids.extend([d.name for d in log_summary_root_dir.iterdir()])
    all_log_ids = sorted(all_log_ids)
    return all_log_ids

@app.route('/')
def index():
    # Define possible root directories
    selected_root_dir = log_root_dirs[0]  # Default selection

    # Get list of log IDs (folder names under selected root directory)
    root_dir = selected_root_dir
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    log_ids = sorted(os.listdir(root_dir), reverse=True)
    selected_log_id = log_ids[0] if log_ids else ''

    # Get list of task IDs for the selected log
    task_ids = []
    selected_task_id = ''
    if selected_log_id:
        task_dir = os.path.join(root_dir, selected_log_id)
        if os.path.exists(task_dir):
            task_ids = sorted(os.listdir(task_dir))
            selected_task_id = task_ids[0] if task_ids else ''

    # Get list of md files for the selected task
    md_files = []
    selected_md_file = ''
    if selected_task_id:
        task_dir = os.path.join(root_dir, selected_log_id, selected_task_id)
        if os.path.exists(task_dir):
            md_files = [f for f in os.listdir(task_dir) if f.endswith('.full.md')]
            md_files.sort()
            selected_md_file = md_files[0] if md_files else ''

    return render_template(
        'index.html',
        root_dirs=[d.name for d in log_root_dirs], 
        selected_root_dir=selected_root_dir,
        log_ids=log_ids,
        selected_log_id=selected_log_id,
        task_ids=task_ids,
        selected_task_id=selected_task_id,
        md_files=md_files,
        selected_md_file=selected_md_file,
        task_level=get_task_level('training', selected_task_id)
    )


@app.route('/logs/<root_dir>')
def get_logs(root_dir):
    # Get list of log IDs under the selected root directory
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    if os.path.exists(root_dir):
        log_ids = sorted(os.listdir(root_dir), reverse=True)
    else:
        log_ids = []
    return jsonify({'logs': log_ids})

@app.route('/tasks/<root_dir>/<log_id>')
def get_tasks(root_dir, log_id):
    # Get list of task IDs under <root_dir>/<log_id>/
    task_dir = os.path.join(root_dir, log_id)
    if os.path.exists(task_dir):
        task_ids = sorted(os.listdir(task_dir))
        task_ids = [task for task in task_ids if task != 'results.txt']        
    else:
        task_ids = []
    return jsonify({'tasks': task_ids})

@app.route('/md_files/<root_dir>/<log_id>/<task_id>')
def get_md_files(root_dir, log_id, task_id):
    # Get list of 'x.full.md' files under <root_dir>/<log_id>/<task_id>/
    task_dir = os.path.join(root_dir, log_id, task_id)
    if os.path.exists(task_dir):
        md_files = [f for f in os.listdir(task_dir) if f.endswith('.full.md')]
        md_files.sort()
    else:
        md_files = []
    return jsonify({'md_files': md_files, 'task_level': get_task_level('training', task_id)})

@app.route('/content/<root_dir>/<log_id>/<task_id>/<md_file_id>')
def get_content(root_dir, log_id, task_id, md_file_id):
    # Read and convert <root_dir>/<log_id>/<task_id>/<md_file_id> to HTML
    md_file = os.path.join(root_dir, log_id, task_id, md_file_id)
    if os.path.exists(md_file):
        with open(md_file, 'r', encoding='utf-8') as file:
            md_content = file.read()
        md_content = re.sub(r'^(.*\(shape=.*\))$', r'<pre>\1</pre>', md_content, flags=re.MULTILINE)
        html_content = markdown.markdown(
            md_content,
            tab_length=2,
            extensions=['fenced_code', 'codehilite', 'nl2br']
        )
        return html_content
    else:
        return 'Content not found.'
    

@app.route('/md_test', methods=['GET', 'POST'])
def md_test():
    html_content = ''
    md_content = ''
    if request.method == 'POST':
        md_content = request.form.get('md_content', '')
        html_content = markdown.markdown(
            md_content,
            tab_length=3,
            extensions=['fenced_code', 'codehilite', 'nl2br']
        )

    return render_template('md_test_index.html', md_content=md_content, html_content=html_content)

@app.route('/solve_fn', methods=['GET', 'POST'])
def solve_fn():
    dataset_ = request.form.get('dataset', 'training')
    task_id_ = request.form.get('task_id', '')
    code_ = ''
    html_content = ''
    if request.method == 'POST':
        code_ = request.form.get('code', '')
        tools_codes = Path(current_file_dir.parent / 'tools_src_mini.py').read_text()
        code2_ = tools_codes + '\n\n' + code_
        outputs = run_task_code_read_outputs_with_timeout(task_id_, LocalDataset(dataset_),
                code2_.encode(), 10, current_file_dir.parent / 'state_machine_solver_code_runner.py')
        for obj in outputs:
            if 'text' in obj:
                html_content += f'<div>{obj["text"]}</div>'
            elif 'grid' in obj:
                html_content += f'<div><img src="data:image/jpeg;base64,{single_grid_to_base64(obj["grid"], draw_edges=False, draw_spine_border=True)}"></div>'
        
        html_content += '<pre>'
        for obj in outputs:
            html_content += f'<div>{obj}</div>'
        html_content += '</pre>'

    return render_template('solve_fn_index.html', dataset=dataset_, task_id=task_id_,
        code=code_, html_content=html_content)

def dict_to_str(d: dict) -> str:
    return f'({", ".join(f"{key}={value}" for key, value in d.items())})'

def dicts_to_str(ds: list[dict]) -> str:
    return '{' + ', '.join(dict_to_str(d) for d in ds) + '}'

def grid_to_lens_html(grid):
    result = f'<div><img src="data:image/jpeg;base64,{single_grid_to_base64(grid, draw_edges=False, draw_spine_border=True)}"></div>'
    objs1 = get_grid_objects_as_flat_list(grid, univalued=True, diagonal=True, with_bg=False, bg_color=0)
    objs2 = get_grid_objects_as_flat_list(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)
    objs3 = get_grid_objects_as_flat_list(grid, univalued=False, diagonal=True, with_bg=False, bg_color=0)
    objs4 = get_grid_objects_as_flat_list(grid, univalued=False, diagonal=False, with_bg=False, bg_color=0)

    desc1 = describe_objects_orthogonal_flat(objs1, univalued=True)
    desc2 = describe_objects_orthogonal_flat(objs2, univalued=True)
    desc3 = describe_objects_orthogonal_flat(objs3, univalued=False)
    desc4 = describe_objects_orthogonal_flat(objs4, univalued=False)

    desc1 = dicts_to_str(desc1)
    desc2 = dicts_to_str(desc2)
    desc3 = dicts_to_str(desc3)
    desc4 = dicts_to_str(desc4)

    objs5 = get_grid_objects_hierarchy(grid)
    desc5 = describe_objects_orthogonal_hierarchy(objs5, univalued=True)
    # def _remove_pos(an_obj):
    #     # an_obj['size'] = len(an_obj['positions'])
    #     # del an_obj['positions']
    #     an_obj['positions'] = len(an_obj['positions'])
    #     for ch_obj in an_obj['children']:
    #         _remove_pos(ch_obj)

    # for obj in objs5:
    #     _remove_pos(obj)

    return f'{result}<br>{desc5}'

    result += f'''<pre>## Automatic grid description
### Objects in the grid get_grid_objects(grid, univalued=True, diagonal=True, with_bg=False, bg_color=0)
{desc1}

### Objects in the get_grid_objects(grid, univalued=True, diagonal=False, with_bg=False, bg_color=0)
{desc2}

### Objects in the get_grid_objects(grid, univalued=False, diagonal=True, with_bg=False, bg_color=0)
{desc3}

### Objects in the get_grid_objects(grid, univalued=False, diagonal=False, with_bg=False, bg_color=0)
{desc4}'''
    
    return result


@app.route('/lens_viewer')
def lens_viewer():
    dataset_ = request.args.get('dataset', 'training')
    task_id_ = request.args.get('task_id', '')
    html_content = ''

    if task_id_ != '':
        task = LocalDataset(dataset_).read_task(task_id_)
            
        for i,sample in enumerate(task["train"], 1):
            html_content += f'<h3>Train pair {i}</h3>'
            html_content += grid_to_lens_html(sample['input'])
            html_content += grid_to_lens_html(sample['output'])
            html_content += '<hr>'
                

        for i,sample in enumerate(task["test"], 1):
            html_content += f'<h3>Test pair {i}</h3>'
            html_content += grid_to_lens_html(sample['input'])
        
    return render_template('lens_index.html', dataset=dataset_, task_id=task_id_,
        html_content=html_content)


@app.route('/any_md')
def any_md():
    html_content = ''
    md_file = request.args.get('md_file', '')
    if Path(md_file).exists():
        md_content = Path(md_file).read_text()
        html_content = markdown.markdown(
            md_content,
            tab_length=3,
            extensions=['fenced_code', 'codehilite', 'nl2br']
        )
    else:
        html_content = 'File not found.'

    return html_content

