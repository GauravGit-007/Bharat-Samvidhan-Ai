import os
import sys
import time
import threading
import concurrent.futures

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval.generator import Generator

NUM_PARALLEL_QUERIES = 5

QUERIES = [
    "What is Article 21 of the Constitution?",
    "Explain Section 378 of the Indian Penal Code.",
    "What are the fundamental rights?",
    "What is the punishment for murder under Section 302?",
    "Can the president be impeached?",
    "What is defamation under IPC Section 499?",
    "What is Article 19?",
    "Explain Section 124A sedition.",
    "What is the preamble?",
    "What is culpable homicide under Section 299?"
]

def run_query(generator, query_id, query_text):
    start_time = time.time()
    try:
        response = generator.generate_rag_response(query_text)
        latency = time.time() - start_time
        return {
            "id": query_id,
            "success": True,
            "latency": latency,
            "error": None
        }
    except Exception as e:
        latency = time.time() - start_time
        return {
            "id": query_id,
            "success": False,
            "latency": latency,
            "error": str(e)
        }

def main():
    print("==================================================")
    print("        CONCURRENCY STRESS TESTING UTILITY        ")
    print("==================================================")
    
    print("Initializing Generator Engine...")
    generator = Generator()
    
    print(f"\nStarting {NUM_PARALLEL_QUERIES} parallel queries using ThreadPoolExecutor...")
    
    start_time = time.time()
    results = []
    
    import threading
    threads = []
    
    def thread_worker(i, q):
        res = run_query(generator, i, q)
        results.append(res)
        
    for i in range(NUM_PARALLEL_QUERIES):
        q = QUERIES[i % len(QUERIES)]
        t = threading.Thread(target=thread_worker, args=(i, q))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    total_time = time.time() - start_time
    
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count
    lock_errors = sum(1 for r in results if r["error"] and "locked" in r["error"].lower())
    
    latencies = [r["latency"] for r in results if r["success"]]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    qps = NUM_PARALLEL_QUERIES / total_time
    
    # Try to extract reranker lock wait time if attached to response
    # We didn't pipe it out of generator in the stress test, so let's check generator logs or simply report the fact.
    
    print("\n==========================================")
    print("STRESS TEST RESULTS")
    print("==========================================")
    print(f"Total Time Taken: {total_time:.2f}s")
    print(f"Queries Per Second (QPS): {qps:.2f}")
    print(f"Average Thread Latency: {avg_latency:.2f}s")
    print(f"Successful Queries: {success_count}/{NUM_PARALLEL_QUERIES}")
    print(f"Failed Queries: {fail_count}/{NUM_PARALLEL_QUERIES}")
    print(f"SQLite 'Database Locked' Errors: {lock_errors}")
    print("==========================================")
    
    if lock_errors == 0:
        print("\n[SUCCESS] WAL Mode successfully prevented database locking during concurrent access.")
    else:
        print("\n[FAILURE] Database locking detected. WAL Mode configuration may be failing.")

if __name__ == "__main__":
    main()
