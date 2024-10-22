from flask import Flask, render_template, jsonify
import os
import markdown

app = Flask(__name__)

@app.route('/')
def index():
    # Define possible root directories
    root_dirs = ['logs', 'important-run-logs']
    selected_root_dir = root_dirs[0]  # Default selection

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
        root_dirs=root_dirs,
        selected_root_dir=selected_root_dir,
        log_ids=log_ids,
        selected_log_id=selected_log_id,
        task_ids=task_ids,
        selected_task_id=selected_task_id,
        md_files=md_files,
        selected_md_file=selected_md_file
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
    return jsonify({'md_files': md_files})

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

if __name__ == '__main__':
    app.run(debug=True)
