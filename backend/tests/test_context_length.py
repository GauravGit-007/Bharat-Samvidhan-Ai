import urllib.request
import json
import traceback

def test_ollama_with_len(length):
    url = "http://localhost:11434/api/generate"
    context = "X " * length
    prompt = f"Context: {context}\n\nQuestion: Hello, answer with 'ok'"
    payload = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 5}
    }
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        print(f"Testing prompt with {length} words...")
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Success for length {length}. Status: {status}")
            return True
    except Exception as e:
        print(f"Failed for length {length}: {e}")
        if hasattr(e, 'read'):
            try:
                print("Error details:", e.read().decode('utf-8'))
            except:
                pass
        return False

if __name__ == "__main__":
    for l in [100, 500, 1000, 2000, 3000]:
        success = test_ollama_with_len(l)
        if not success:
            print("Crashed!")
            break
