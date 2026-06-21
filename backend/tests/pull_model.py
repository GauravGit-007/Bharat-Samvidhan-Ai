import urllib.request
import json
import time
import sys

def pull_model(model_name="llama3.1:8b"):
    print(f"Starting to pull model '{model_name}' via Ollama API...")
    url = "http://localhost:11434/api/pull"
    data = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
    
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            last_pct = -1
            for line in response:
                if not line:
                    continue
                status_data = json.loads(line.decode("utf-8"))
                status = status_data.get("status", "")
                completed = status_data.get("completed", 0)
                total = status_data.get("total", 0)
                
                if total > 0:
                    pct = int((completed / total) * 100)
                    if pct != last_pct:
                        sys.stdout.write(f"\rPulling {model_name}: {pct}% ({completed}/{total} bytes) - {status}")
                        sys.stdout.flush()
                        last_pct = pct
                else:
                    sys.stdout.write(f"\rStatus: {status}                     ")
                    sys.stdout.flush()
            print(f"\nSuccessfully pulled model '{model_name}'!")
            return True
    except Exception as e:
        print(f"\nError pulling model: {e}")
        return False

if __name__ == "__main__":
    pull_model()
