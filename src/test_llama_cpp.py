import requests
import json

# make llama.cpp and run llama-server
# ssh with port forwarding to server
url = "http://localhost:8080/v1/chat/completions"
payload = {
    "max_tokens": 20480,
    "top_p": 1,
    "top_k": 40,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "temperature": 0.6,
    "messages": [
        {'role': 'user', 'content': 'proof 1+1 is 2'}
    ]
}
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
print("Response Text:", response.text)

# If you expect a JSON response, parse it
try:
    response_json = response.json()
    print("Response JSON:", response_json)
except json.JSONDecodeError:
    print("Failed to parse JSON response")