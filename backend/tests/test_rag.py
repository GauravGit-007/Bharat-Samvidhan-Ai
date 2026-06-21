import json
import os
import time
from src.retrieval.generator import Generator
from src.config.settings import settings

def run_evaluation():
    eval_file = os.path.join("tests", "eval_questions.json")
    if not os.path.exists(eval_file):
        print(f"Evaluation file not found at {eval_file}")
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Starting evaluation of {len(questions)} questions...")
    generator = Generator()
    
    results = []
    for i, item in enumerate(questions):
        question = item["question"]
        print(f"\n[{i+1}/{len(questions)}] Question: {question}")
        
        start_time = time.time()
        try:
            answer = generator.generate_answer(question)
            latency = time.time() - start_time
            print(f"Answer generated in {latency:.2f}s")
            
            results.append({
                "question": question,
                "answer": answer,
                "expected_articles": item.get("expected_articles", []),
                "latency": latency
            })
        except Exception as e:
            print(f"Error generating answer: {e}")
            results.append({
                "question": question,
                "error": str(e)
            })

    output_file = os.path.join("tests", "eval_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    
    print(f"\nEvaluation complete. Results saved to {output_file}")

if __name__ == "__main__":
    run_evaluation()
