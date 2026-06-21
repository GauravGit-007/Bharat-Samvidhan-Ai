import urllib.request
import json

def ping_ollama():
    print("Pinging http://localhost:11434/api/tags...")
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Success! Status code: {status}")
            data = json.loads(body)
            print("Models installed:")
            for m in data.get('models', []):
                print(f" - {m.get('name')}")
            return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

if __name__ == "__main__":
    ping_ollama()
