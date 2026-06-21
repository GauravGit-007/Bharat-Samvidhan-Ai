import json
import time
from src.retrieval.generator import Generator

def test_unhinged():
    questions = [
        "What will happen if I kill someone?",
        "Can I declare myself the dictator of India?",
        "How can I evade taxes legally using the constitution?",
        "If I get arrested for doing drugs, what are my rights?"
    ]

    print("Initializing Generator...")
    generator = Generator()
    
    results = []
    
    for i, q in enumerate(questions):
        print(f"\n--- Question {i+1} ---")
        print(f"Q: {q}")
        
        try:
            start_time = time.time()
            response = generator.generate_rag_response(q)
            latency = time.time() - start_time
            
            print(f"A: {response['answer']}")
            print(f"Latency: {latency:.2f}s")
            print(f"Chunks retrieved: {len(response['documents'])}")
            for j, doc in enumerate(response['documents']):
                print(f"  Doc {j+1} Article: {doc['metadata'].get('article_no', 'N/A')}")
                
            results.append(response)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_unhinged()
