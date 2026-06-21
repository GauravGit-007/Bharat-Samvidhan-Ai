import os
import sys

# Ensure PYTHONPATH includes the workspace root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.retrieval.generator import Generator

def main():
    print("==================================================")
    print("      BHARAT SAMVIDHAN AI - TERMINAL CLIENT       ")
    print("==================================================")
    print("Initializing RAG Engine (please wait)...")
    try:
        generator = Generator()
        print("System initialized. Type your query and press Enter.")
        print("Type 'exit' or 'quit' to close the client.\n")
    except Exception as e:
        print(f"Failed to initialize RAG Generator: {e}")
        print("Please check if Ollama is running and has the model installed.")
        return

    chat_history = []
    
    while True:
        try:
            query = input("\nCitizen ⚖️ > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            print("Analyzing query and retrieving citations...")
            response = generator.generate_rag_response(query, chat_history=chat_history)
            
            # Print citations
            print("\n--------------------------------------------------")
            print(f"Retrieved Legal Citations ({len(response['documents'])}):")
            for idx, doc in enumerate(response["documents"][:5]): # Show top 5 citations
                doc_type = "IPC Section" if doc["metadata"].get("type") == "ipc_section" else "Constitution Article"
                ref_no = doc["metadata"].get("article_no") or doc["metadata"].get("section_no") or "N/A"
                print(f" [{idx + 1}] {doc_type} {ref_no} (Part/Chapter: {doc['metadata'].get('part', doc['metadata'].get('chapter', 'N/A'))})")
            if len(response["documents"]) > 5:
                print(f" ... and {len(response['documents']) - 5} more.")
            print("--------------------------------------------------")
            
            # Print answer
            print(f"\nBharat Samvidhan AI:\n{response['answer']}")
            print(f"\n(Pipeline Latency: {response['latency']}s)")
            
            # Update history for conversational context window
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": response["answer"]})
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"Error processing query: {e}")

if __name__ == "__main__":
    main()
