# Implementation Plan - Retrieval Quality, Latency Profiling & Evaluation Calibration

This plan addresses the critical RAG architecture and evaluation gaps identified in the current system. It outlines the integration of local cross-encoder reranking, evaluation precision metrics, LLM-as-a-judge model calibration, negative test cases, latency profiling, and concurrency stress testing.

---

## Proposed Changes

### 1. Local Reranker Integration (Cross-Encoder)
* **Goal**: Reduce context noise, prevent LLM attention dilution, and improve final response accuracy.
* **Settings Update**: Add `RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"` and `USE_RERANKER = True` to [settings.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/config/settings.py).
* **Retriever Update**: 
  - Add a lazy-loaded `rerank` method to [retriever.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/retrieval/retriever.py) using `sentence_transformers.CrossEncoder`.
  - Modify `get_relevant_documents` to run the reranker on the fused dense + sparse document candidates list (e.g. top 15) and select the top 5.
  - Perform adjacent document fetching on only the top 2 *reranked* documents to keep context compact and highly relevant.

### 2. Enhanced Evaluation Metrics & Regression Gates
* **Goal**: Track token dilution cost (precision) and ensure corpus expansions do not regress search accuracy.
* **Precision Metric**: In [run_rigorous_tests.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/run_rigorous_tests.py) and [monte_carlo_test.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/monte_carlo_test.py), compute **Citation Precision**:
  $$\text{Citation Precision} = \frac{\text{Expected Citations found in } R}{\text{Total retrieved document chunks}}$$
* **Regression Gate**: Add an explicit check in the test runner. If the average recall of the original 11 test cases drops below a `90.0%` threshold, trigger a prominent regression alert in the ledger and console.

### 3. LLM-as-a-Judge Model Calibration
* **Goal**: Avoid unreliable, hallucinated evaluations from the local 1B parameters model.
* **Judge Scan**: In [run_rigorous_tests.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/run_rigorous_tests.py), add a model scan that queries Ollama API tags for larger available models (e.g., `llama3:8b`, `llama3.1:8b`, `mistral:7b`, `gemma2:9b`).
* **Calibration**: If a larger model is found, use it specifically for the `query_judge` evaluator. If only the 1B model is present, execute evaluation but output a clear console warning.

### 4. Negative (Out-of-Scope) Test Cases
* **Goal**: Verify that the RAG pipeline declines to answer or flags missing citations for irrelevant queries instead of hallucinating.
* **Test Cases**: Add two out-of-scope negative cases to `TEST_CASES` (e.g., US copyright procedures, Canadian drone speed limits) expecting `[]` citations. The judge will verify if the system refuses or flags the lack of reference material.

### 5. Latency Profiling & Generation Blocker Highlight
* **Goal**: Expose that generation/synthesis is the primary bottleneck (99%+ of total latency) so development resources are targeted appropriately.
* **Profiling**: Update [run_rigorous_tests.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/run_rigorous_tests.py) to display a distinct breakdown of **Retrieval Stage Latency (ms)** vs. **Generation Stage Latency (seconds)** in the console summary.

### 6. Concurrency & Stress Testing
* **Goal**: Provide empirical data for WAL optimization performance under concurrent traffic.
* **Stress Script**: Create a new test utility `tests/stress_test_concurrency.py` that fires 10 parallel queries concurrently, measuring queries per second (QPS) and ensuring zero SQLite locking errors.

---

## Proposed File Actions

### [MODIFY] [settings.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/config/settings.py)
* Add settings variables for `RERANK_MODEL` and `USE_RERANKER`.

### [MODIFY] [retriever.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/retrieval/retriever.py)
* Integrate local `sentence-transformers` Cross-Encoder reranker.

### [MODIFY] [run_rigorous_tests.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/run_rigorous_tests.py)
* Add precision calculations, negative cases, judge model calibration scan, and latency profiling.

### [MODIFY] [monte_carlo_test.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/monte_carlo_test.py)
* Include precision metrics.

### [NEW] [stress_test_concurrency.py](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/tests/stress_test_concurrency.py)
* Stress test tool to verify locks and throughput.

---

## Verification Plan

### Evaluation Metrics
* Run `python tests/run_rigorous_tests.py` and verify:
  1. Average recall remains above `90.0%`.
  2. Average precision is logged correctly.
  3. Latency breakdown is clearly visible.
  4. Out-of-scope negative cases execute cleanly.

### Stress Verification
* Run `python tests/stress_test_concurrency.py` and confirm 10 concurrent requests return zero SQLite write/read errors.
