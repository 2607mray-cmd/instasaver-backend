import requests
import json

url = "https://www.youtube.com/watch?v=cyGeCPA_AAw"

print(f"Testing URL: {url}")

try:
    response = requests.post("http://localhost:8000/info", json={"url": url})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Failed!")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
