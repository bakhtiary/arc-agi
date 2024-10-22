from flask import Flask, request, jsonify
from multiprocessing import Process, Queue
import multiprocessing
import time
import queue

app = Flask(__name__)

def execute_code_snippet(code_snippet, output_queue):
    try:
        exec_globals = {}
        exec_locals = {}
        exec(code_snippet, exec_globals, exec_locals)
        result = exec_locals.get('result', None)
        output_queue.put(result)
    except Exception as e:
        output_queue.put(f'Error: {e}')

@app.route('/execute', methods=['POST'])
def execute_code():
    code_snippet = request.form.get('code', '')
    if not code_snippet:
        return jsonify({'error': 'No code provided.'}), 400

    output_queue = multiprocessing.Queue()
    process = Process(target=execute_code_snippet, args=(code_snippet, output_queue))
    process.start()

    # Wait for the result with a timeout of 15 seconds
    try:
        result = output_queue.get(timeout=15)
    except queue.Empty:
        result = 'Error: Execution timed out.'
    finally:
        process.terminate()
        process.join()

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(port=5001)
