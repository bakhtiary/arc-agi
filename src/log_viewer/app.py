from collections import defaultdict
from pathlib import Path
from flask import Flask, render_template, jsonify
import os
import markdown
from calc_logs_statistics import get_log_summary_by_experiments, get_log_summary_by_tasks, log_summary_to_ladder

app = Flask(__name__)

log_root_dirs = [Path('important-run-logs')]
log_summary = get_log_summary_by_tasks(log_root_dirs)
log_ladder = log_summary_to_ladder(log_summary)

def get_task_level(dataset, task_id):
    if task_id not in log_summary[dataset]:
        return 'n/a'
    
    sum_score = sum(score for root_dir, log_dir, score in log_summary[dataset][task_id])
    return f'{sum_score} / {len(log_summary[dataset][task_id])}'


@app.route('/task_summary')
def task_summary():
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
    if len(all_log_ids) > len("abcdefghijklmnopqrstuvwxyz"):
        raise Exception('Too many logs to show in task summary')
    log_id_symbols = dict(zip(all_log_ids, list("abcdefghijklmnopqrstuvwxyz")))

    log_summary_exp = get_log_summary_by_experiments(log_root_dirs)
    def tr_order(e):
        return ['success_ok', 'success_nok', 'error', 'timeout', 'n/a'].index(e[0])
    
    html += f'<h1>Task summary based on aggregate of <i>{log_root_dirs}</i></h1>'
    html += '<h2>Legend</h2>'
    for log_id, rest in log_summary_exp.items():
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
                    a_class = 'succ' if score != 0 else 'fail'
                    a_tags.append(f'<a class="{a_class}" href="/#{root_dir.name}/{log_id}/{task_id}/1.full.md">{log_id_symbols[log_id]}</a>')
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
        return ['success_ok', 'success_nok', 'error', 'timeout', 'n/a'].index(e[0])
    
    html += f'<h1>Experiment summary based on aggregate of <i>{log_root_dirs}</i></h1><hr>'
    for log_id, rest in log_summary_exp.items():
        summary = ', '.join([f'{tr}: {len(task_ids)}' for tr, task_ids in sorted(rest.items(),key=tr_order)])
        html += f'<h2>{log_id} ({summary})</h2>'
        for tr, task_ids in rest.items():
            html += f'<h3>{tr}</h3>'
            for task_id in task_ids:
                # Todo, hardcoded root dir
                html += f'<a href="/#important-run-logs/{log_id}/{task_id}/1.full.md">{task_id}</a> '
        html += '<hr>'
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
        html_content = markdown.markdown(
            md_content,
            extensions=['fenced_code', 'codehilite']
        )
        return html_content
    else:
        return 'Content not found.'

