from src.retrieval.generator import Generator
import traceback
import sys

def test():
    # Force UTF-8 printing for Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except:
            pass

    try:
        print("Instantiating Generator...")
        gen = Generator()
        print("Generator instantiated. Invoking LLM...")
        prompt = "Explain Article 14 of the Constitution."
        print(f"Prompt: {prompt}")
        # Try direct llm invocation first
        print("Direct LLM invocation:")
        res = gen.llm.invoke(prompt)
        print("Result:", res)
    except Exception as e:
        print("Direct LLM invocation failed:")
        traceback.print_exc()

    try:
        print("\nRAG Response invocation:")
        res = gen.generate_rag_response("Explain Article 14 of the Constitution.")
        print("RAG Answer:")
        print(res["answer"])
        print("\nAll checks in test_generator_direct completed successfully!")
    except Exception as e:
        print("RAG Response invocation failed:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
