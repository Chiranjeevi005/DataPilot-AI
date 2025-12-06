
import requests
import io
import os

url = 'http://localhost:5328/api/upload'
files = {'file': ('test.csv', 'col1,col2\n1,2', 'text/csv')}

try:
    print(f"Uploading to {url}...")
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
