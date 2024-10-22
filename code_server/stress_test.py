import requests
import time
import threading

NUM_REQUESTS = 100  # Total number of requests to send
CONCURRENT_THREADS = 10  # Number of concurrent threads

# The code snippet to execute
code_snippet = '''
result = sum(range(1000))
'''

# The URL of the server
SERVER_URL = 'http://localhost:5001/execute'

# Function to send a POST request and measure response time
def send_request(times):
    start_time = time.time()
    response = requests.post(SERVER_URL, data={'code': code_snippet})
    end_time = time.time()
    times.append(end_time - start_time)
    if response.status_code != 200:
        print(f'Error: {response.status_code}, {response.text}')

def worker(times, num_requests):
    for _ in range(num_requests):
        send_request(times)

def main():
    times = []
    threads = []
    requests_per_thread = NUM_REQUESTS // CONCURRENT_THREADS

    start_time = time.time()

    for _ in range(CONCURRENT_THREADS):
        thread = threading.Thread(target=worker, args=(times, requests_per_thread))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_time = time.time() - start_time
    average_response_time = sum(times) / len(times)
    print(f'Total time for {NUM_REQUESTS} requests: {total_time:.2f} seconds')
    print(f'Average response time: {average_response_time:.4f} seconds')

if __name__ == '__main__':
    main()
