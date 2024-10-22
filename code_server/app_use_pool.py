from flask import Flask, request, jsonify
from multiprocessing import Process, Queue, Manager
import multiprocessing
import time
import threading
import queue

app = Flask(__name__)

# Manager for shared state between processes
manager = Manager()
worker_heartbeats = manager.dict()

class Worker:
    def __init__(self, id):
        self.id = id
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.process = Process(
            target=self.run,
            args=(self.input_queue, self.output_queue, worker_heartbeats, self.id)
        )
        self.process.daemon = True
        self.process.start()

    @staticmethod
    def run(input_queue, output_queue, heartbeats, id):
        while True:
            # Update heartbeat
            heartbeats[id] = time.time()
            try:
                # Try to get code snippet to execute
                code_snippet = input_queue.get(timeout=1)
                # Execute the code snippet safely
                exec_globals = {}
                exec_locals = {}
                exec(code_snippet, exec_globals, exec_locals)
                result = exec_locals.get('result', None)
                output_queue.put(result)
            except queue.Empty:
                # No code to execute, continue heartbeat
                pass
            except Exception as e:
                # Return any execution errors
                output_queue.put(f'Error: {e}')
            time.sleep(1)

    def is_alive(self):
        return self.process.is_alive()

    def terminate(self):
        self.process.terminate()
        self.process.join()

# Create a pool of worker processes
workers = [Worker(i) for i in range(4)]

def monitor_workers():
    while True:
        for worker in workers:
            last_heartbeat = worker_heartbeats.get(worker.id, 0)
            if time.time() - last_heartbeat > 15:
                print(f'Worker {worker.id} is unresponsive. Restarting...')
                worker.terminate()
                workers.remove(worker)
                # Restart the worker
                new_worker = Worker(worker.id)
                workers.append(new_worker)
        time.sleep(5)

# Start the worker monitoring thread
monitor_thread = threading.Thread(target=monitor_workers)
monitor_thread.daemon = True
monitor_thread.start()

def get_available_worker():
    # Returns the first available worker
    while True:
        for worker in workers:
            if worker.input_queue.empty() and worker.output_queue.empty():
                return worker
        time.sleep(0.1)  # Slight delay to prevent busy waiting

@app.route('/execute', methods=['POST'])
def execute_code():
    code_snippet = request.form.get('code', '')
    if not code_snippet:
        return jsonify({'error': 'No code provided.'}), 400

    # Assign the code snippet to an available worker
    worker = get_available_worker()
    worker.input_queue.put(code_snippet)

    # Wait for the result with a timeout of 15 seconds
    try:
        result = worker.output_queue.get(timeout=15)
    except queue.Empty:
        result = 'Error: Execution timed out.'

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(port=5001)
