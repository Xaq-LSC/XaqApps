import requests
from requests.auth import HTTPBasicAuth

# VLC HTTP config
VLC_URL = "http://localhost:8080/requests/status.json"
USERNAME = "user"
PASSWORD = "vlcpass"

try:
    # Trigger playback
    response = requests.get(
        VLC_URL,
        params={"command": "pl_play"},
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        timeout=3
    )
    if response.status_code == 200:
        print("Play command sent successfully.")
    else:
        print(f"VLC responded with status code {response.status_code}")
except Exception as e:
    print(f"Failed to send play command: {e}")
