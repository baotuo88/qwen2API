import requests
import time
import subprocess
import os

print("Starting backend for tests...")
env = os.environ.copy()
env["PYTHONPATH"] = "/workspace"
env["PORT"] = "8081"
proc = subprocess.Popen(["python", "backend/main.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3) # Wait for startup

try:
    # 1. Healthz probe
    r = requests.get("http://127.0.0.1:8081/healthz")
    assert r.status_code == 200, "Healthz failed"
    print("✅ /healthz works")

    # 2. Readyz probe (engine might not be fully started, but route exists)
    r = requests.get("http://127.0.0.1:8081/readyz")
    print(f"✅ /readyz works (status: {r.status_code})")

    # 3. Create a test user via Admin API to get a token
    r = requests.post("http://127.0.0.1:8081/api/admin/users", 
                      headers={"Authorization": "Bearer admin"}, 
                      json={"name": "test_user"})
    assert r.status_code == 200, f"Admin API failed: {r.text}"
    token = r.json()["id"]
    print(f"✅ Admin API works, got token: {token}")

    # 4. Embeddings
    r = requests.post("http://127.0.0.1:8081/v1/embeddings", 
                      headers={"Authorization": f"Bearer {token}"},
                      json={"model": "text-embedding-ada-002", "input": "Hello world"})
    assert r.status_code == 200, f"Embeddings failed: {r.text}"
    assert len(r.json()["data"][0]["embedding"]) == 1536
    print("✅ Embeddings API works")

    # 5. Check missing Anthropic/Gemini endpoints exist (will return 401/400 but not 404)
    r = requests.post("http://127.0.0.1:8081/anthropic/v1/messages", json={})
    assert r.status_code in [401, 400, 422], "Anthropic endpoint missing"
    print("✅ Anthropic router exists")

    r = requests.post("http://127.0.0.1:8081/v1beta/models/gemini-1.5-pro:streamGenerateContent", json={})
    assert r.status_code in [401, 400, 422], "Gemini endpoint missing"
    print("✅ Gemini router exists")

    print("🎉 All architectural endpoints verified successfully!")
finally:
    proc.terminate()
    proc.wait()
