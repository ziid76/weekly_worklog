import requests
import os
from dotenv import load_dotenv

load_dotenv()

embed_access_url = os.environ.get('EMBED_ACCESS_URL', 'http://152.70.250.31')
embed_key = os.environ.get('EMBED_ACCESS_KEY', '')
url = f"{embed_access_url}/web-monitor/api/dashboard_data/?key={embed_key}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print(f"Requesting URL: {url}")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.text[:500]}")
    if response.status_code == 200:
        try:
            print("JSON check: OK")
            response.json()
        except Exception as e:
            print(f"JSON parse error: {e}")
except Exception as e:
    print(f"Request Error: {e}")
