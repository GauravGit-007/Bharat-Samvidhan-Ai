import urllib.request
import json
import traceback

def test_model(model_name):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": "Hello",
        "stream": False
    }
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        print(f"Pinging generate for {model_name}...")
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Status for {model_name}: {status}")
            data = json.loads(body)
            print("Response:", data.get("response"))
            return True
    except Exception as e:
        print(f"Failed for {model_name}: {e}")
        if hasattr(e, 'read'):
            try:
                print("Error details:", e.read().decode('utf-8'))
            except:
                pass
        return False

if __name__ == "__main__":
    print("Testing llama3.1:8b...")
    test_model("llama3.1:8b")
    print("\nTesting llama3.2:1b...")
    test_model("llama3.2:1b")
