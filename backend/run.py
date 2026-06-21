import os
import sys
import time
import socket
import subprocess
import webbrowser
import threading

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(("127.0.0.1", port))
            return True
        except socket.error:
            return False

def open_browser(url):
    time.sleep(2.5)
    print("\n[*] Opening web browser...")
    webbrowser.open(url)

def main():
    print("==================================================")
    print("      BHARAT SAMVIDHAN AI - LOCAL LAUNCHER        ")
    print("==================================================")
    
    # 1. Check if Ollama is running
    print("[*] Checking Ollama status...")
    if is_port_open(11434):
        print("  - Ollama is running successfully on port 11434.")
    else:
        print("  - [WARNING] Ollama is not detected on port 11434.")
        print("    Please start the Ollama application or service manually.")
        print("    (The RAG system will use fallback reference mode if Ollama is offline.)")
        
    # 2. Check if frontend build exists
    script_dir = os.path.dirname(os.path.abspath(__file__)) # root/backend
    root_dir = os.path.dirname(script_dir) # root
    dist_path = os.path.abspath(os.path.join(root_dir, "frontend", "dist"))
    
    if not os.path.exists(dist_path):
        print("[*] Frontend distribution not found. Building frontend static files...")
        try:
            # Check for npm and run build
            frontend_dir = os.path.join(root_dir, "frontend")
            subprocess.run("npm run build", shell=True, cwd=frontend_dir, check=True)
            print("  - Frontend built successfully!")
        except Exception as e:
            print(f"  - [Error] Failed to build frontend: {e}")
            print("    Please ensure Node.js/NPM is installed and run 'npm install' and 'npm run build' inside 'frontend'.")
            sys.exit(1)
            
    # 3. Open browser after startup
    url = "http://127.0.0.1:8000/"
    print(f"[*] Application URL: {url}")
    print("[*] Launching your web browser automatically...")
    
    # Open browser in a separate background thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    
    # 4. Start FastAPI Backend serving both API and static UI
    print("[*] Starting unified server (Uvicorn)...")
    os.environ["PYTHONPATH"] = "."
    try:
        # Run uvicorn inside backend directory so it finds backend/src and backend/data
        subprocess.run([sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=script_dir, check=True)
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n[Error] Failed to run uvicorn server: {e}")
        print("Please verify that Python packages listed in 'requirements.txt' are installed.")

if __name__ == "__main__":
    main()
