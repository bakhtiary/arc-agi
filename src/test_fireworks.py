import requests
import json


print("Response Text:", response.text)

# If you expect a JSON response, parse it
try:
    response_json = response.json()
    print("Response JSON:", response_json)
except json.JSONDecodeError:
    print("Failed to parse JSON response")