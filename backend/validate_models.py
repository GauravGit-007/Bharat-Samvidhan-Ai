import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

# Load environmental configurations
load_dotenv()

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "-"))
    print("=" * 60)

def test_ollama():
    print_section("testing local ollama service")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"[*] Base URL: {ollama_url}")
    
    # Check server availability
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.getcode() == 200:
                body = response.read().decode('utf-8')
                data = json.loads(body)
                models = data.get("models", [])
                
                print("[SUCCESS] LOCAL OLLAMA SERVER IS ONLINE.")
                print(f"[*] Found {len(models)} installed model(s):")
                for m in models:
                    name = m.get("name", "Unknown")
                    size = m.get("size", 0) / (1024 * 1024 * 1024) # GB
                    print(f"    - {name} ({size:.2f} GB)")
                return True
            else:
                print(f"[FAIL] Ollama server returned HTTP {response.getcode()}")
    except Exception as e:
        print(f"[FAIL] FAILED TO CONNECT TO OLLAMA SERVER: {e}")
        print("    Ensure the Ollama application is running on your machine.")
    return False

def test_groq():
    print_section("testing groq cloud api service")
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key") or ""
    
    if not api_key:
        print("[FAIL] GROQ_API_KEY NOT FOUND IN ENVIRONMENT OR .ENV FILE.")
        print("    To run cloud models, add GROQ_API_KEY=gsk_... to your .env file.")
        return False
        
    print(f"[SUCCESS] GROQ_API_KEY is configured (Length: {len(api_key)}, Prefix: {api_key[:8]}...)")
    
    # Try importing groq and running a test
    try:
        import groq
    except ImportError:
        print("[FAIL] groq library is not installed. Run 'pip install groq'.")
        return False
        
    # Test Llama-3.1-8b-instant (Fast, low quota consumption)
    print("[*] Testing Groq model: llama-3.1-8b-instant...")
    try:
        client = groq.Groq(api_key=api_key)
        import time
        t0 = time.time()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hi"}],
            max_completion_tokens=5,
            temperature=0.1
        )
        latency = time.time() - t0
        content = completion.choices[0].message.content.strip()
        print(f"[SUCCESS] llama-3.1-8b-instant is fully functional!")
        print(f"    - Latency: {latency:.2f}s")
        print(f"    - Output: \"{content}\"")
    except Exception as e:
        print(f"[FAIL] llama-3.1-8b-instant test failed: {e}")
        return False
        
    # Test Llama-3.3-70b-versatile (Primary high quality model)
    print("\n[*] Testing Groq model: llama-3.3-70b-versatile...")
    try:
        t0 = time.time()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hi"}],
            max_completion_tokens=5,
            temperature=0.1
        )
        latency = time.time() - t0
        content = completion.choices[0].message.content.strip()
        print(f"[SUCCESS] llama-3.3-70b-versatile is fully functional!")
        print(f"    - Latency: {latency:.2f}s")
        print(f"    - Output: \"{content}\"")
    except Exception as e:
        print(f"[WARNING] llama-3.3-70b-versatile failed: {e}")
        print("    (The system will automatically fall back to llama-3.1-8b-instant during rate limits)")
        
    return True

def main():
    print("=" * 60)
    print("         BHARAT SAMVIDHAN AI - MODEL VALIDATION SCRIPT       ")
    print("=" * 60)
    
    ollama_ok = test_ollama()
    groq_ok = test_groq()
    
    print_section("summary results")
    print(f"Local Ollama: {'[SUCCESS] Available' if ollama_ok else '[FAIL] Offline'}")
    print(f"Groq Cloud:   { '[SUCCESS] Configured & Working' if groq_ok else '[FAIL] Not Working / Key Missing'}")
    print("-" * 60)
    
    if not ollama_ok and not groq_ok:
        print("[FAIL] WARNING: Neither Local Ollama nor Groq API is functioning.")
        print("    The RAG system will fall back to Vector Index Reference Synthesis only.")
        sys.exit(1)
    else:
        print("[SUCCESS] Ready: At least one LLM generation engine is available.")
        sys.exit(0)

if __name__ == "__main__":
    main()
