import requests, json
import time
import os

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
ENDPOINT_ID = os.getenv("ENDPOINT_ID")

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
            "input": {
            "prompt": "Hello World"
            }
            }

response = requests.post(url, headers=headers, data=json.dumps(payload))
job_data = response.json()
print("Job created:", job_data)

job_id = job_data.get("id")
if not job_id:
    raise RuntimeError(f"Failed to start job: {job_data}")

# ---- 2. Poll for status ----
STATUS_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"

while True:
    status_resp = requests.get(STATUS_URL, headers=headers)
    data = status_resp.json()
    print(data)  # show progress info

    status = data.get("status")
    if status == "COMPLETED":
        print("\n✅ Job done! Output:", data.get("output"))
        break
    elif status in ["FAILED", "CANCELLED"]:
        print("\n❌ Job failed:", data)
        break

    time.sleep(3)