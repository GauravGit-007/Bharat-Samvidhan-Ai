import json
import urllib.request
import urllib.error
import sys
import time

def test_streaming():
    url = "http://localhost:8000/api/query/stream"
    payload = {
        "query": "What is Article 21 of the Indian Constitution?",
        "chat_history": []
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Connecting to streaming route {url}...")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"Connected! Status: {response.getcode()}")
            print("Reading Server-Sent Events stream:")
            
            event_type = None
            documents_received = False
            tokens_count = 0
            done_received = False
            latency = 0.0
            
            # Read line-by-line
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                
                if line_str.startswith("event:"):
                    event_type = line_str.replace("event:", "").strip()
                elif line_str.startswith("data:"):
                    data_raw = line_str.replace("data:", "").strip()
                    try:
                        data = json.loads(data_raw)
                        if event_type == "documents":
                            documents_received = True
                            print(f"\n[EVENT: documents] Retrieved {len(data)} citations.")
                        elif event_type == "token":
                            tokens_count += 1
                            print(data, end="", flush=True)
                        elif event_type == "done":
                            done_received = True
                            latency = data.get("latency", 0.0)
                            print(f"\n[EVENT: done] Execution completed in {latency}s.")
                    except Exception as e:
                        print(f"\nError decoding SSE data block: {e}")
            
            print("\n-------------------------------------------")
            print("STREAMING TEST RESULTS")
            print("-------------------------------------------")
            print(f"Documents Retrieved Event: {'PASS' if documents_received else 'FAIL'}")
            print(f"Token Chunks Streamed: {tokens_count} tokens")
            print(f"Done Event Received: {'PASS' if done_received else 'FAIL'}")
            print(f"Client-Side Measured Time: {time.time() - start_time:.2f}s")
            print("-------------------------------------------")
            
            if documents_received and tokens_count > 0 and done_received:
                print("All streaming checks PASSED!")
                sys.exit(0)
            else:
                print("Streaming checks FAILED!")
                sys.exit(1)
                
    except urllib.error.URLError as e:
        print(f"URL Error: {e}")
        print("Please check if the FastAPI server is running at http://localhost:8000/")
        sys.exit(1)
    except Exception as e:
        print(f"General Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_streaming()
