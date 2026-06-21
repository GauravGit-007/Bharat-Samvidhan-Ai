import os
import sys
import random
import re
import time
import math
import argparse

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval.retriever import Retriever
from src.retrieval.generator import Generator

def get_percentile(data, pct):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

def clean_document_text(text):
    # Remove metadata headers like [Indian Penal Code] Section 378: Theft
    text = re.sub(r'^\[[^\]]+\]\s*(?:Section|Article)\s*[^:]+:\s*', '', text, flags=re.IGNORECASE)
    # Remove Preamble / Part headers
    text = re.sub(r'^(?:PART|PREAMBLE)\s+[IVXLCD]+.*?\n', '', text, flags=re.IGNORECASE)
    return text.strip()

def extract_random_phrase(text):
    clean_text = clean_document_text(text)
    # Split into lines or sentences
    segments = re.split(r'\.|\n|;', clean_text)
    # Filter out empty or extremely short segments
    valid_segments = []
    for s in segments:
        s_clean = s.strip()
        words = s_clean.split()
        if len(words) >= 6 and len(words) <= 25:
            # Avoid list item indicators or digits at start
            if not re.match(r'^\(?[0-9a-zA-Z]\)?\s*$', words[0]) and not s_clean.startswith("Provided"):
                valid_segments.append(s_clean)
                
    if not valid_segments:
        # Fallback to a sub-phrase of the first line
        words = clean_text.split()
        if len(words) > 10:
            start = random.randint(0, len(words) - 10)
            return " ".join(words[start:start + 10])
        return clean_text[:100]
        
    return random.choice(valid_segments)

def generate_monte_carlo_query(doc):
    doc_type = doc.metadata.get("type", "")
    art_no = str(doc.metadata.get("article_no", ""))
    act_name = doc.metadata.get("act_name", "Indian Constitution")
    
    phrase = extract_random_phrase(doc.page_content)
    # Clean the phrase slightly (remove double quotes, ending periods)
    phrase = phrase.strip(' .,"\'')
    
    query_type = random.choice(["citation", "semantic", "hybrid"])
    
    if query_type == "citation":
        if doc_type == "article":
            templates = [
                f"What is Article {art_no} of the Indian Constitution?",
                f"Can you explain Article {art_no}?",
                f"What are the provisions under Article {art_no}?"
            ]
        else:
            templates = [
                f"What is Section {art_no} of the {act_name}?",
                f"Explain the legal provision under Section {art_no} of the {act_name}.",
                f"What does Section {art_no} state?"
            ]
        return random.choice(templates)
        
    elif query_type == "semantic":
        templates = [
            f"What does the law say about: {phrase}?",
            f"What is the legal rule regarding {phrase}?",
            f"Is there a penalty or guideline for {phrase}?",
            f"How does the legal code address {phrase}?"
        ]
        return random.choice(templates)
        
    else:  # hybrid
        if doc_type == "article":
            templates = [
                f"Under Article {art_no}, how does the Constitution handle {phrase}?",
                f"Explain Article {art_no} in the context of {phrase}."
            ]
        else:
            templates = [
                f"Under Section {art_no} of {act_name}, what is the rule about {phrase}?",
                f"Explain Section {art_no} in relation to {phrase}."
            ]
        return random.choice(templates)

def main():
    parser = argparse.ArgumentParser(description="Monte Carlo RAG Evaluation Suite")
    parser.add_argument("--trials", type=int, default=100, help="Number of random queries to run")
    parser.add_argument("--e2e", type=int, default=5, help="Number of full end-to-end LLM trials to run")
    args = parser.parse_args()
    
    print("==================================================")
    print("        MONTE CARLO RAG TESTING SUITE             ")
    print("==================================================")
    
    print("Initializing RAG Engines...")
    generator = Generator()
    retriever = generator.retriever
    
    if not retriever.all_docs:
        print("[Error] No documents loaded in retriever. Ensure databases are ingested.")
        sys.exit(1)
        
    print(f"Loaded {len(retriever.all_docs)} total documents in retriever corpus.")
    
    print(f"\nStarting {args.trials} Monte Carlo Retrieval Trials...")
    
    recall_matches = []
    precision_scores = []
    latencies = []
    
    for i in range(args.trials):
        # 1. Randomly sample document from the corpus
        source_doc = random.choice(retriever.all_docs)
        
        # 2. Generate random query based on document
        query = generate_monte_carlo_query(source_doc)
        
        # 3. Route query to get the domain
        domain = generator.route_query(query)
        
        # 4. Query RAG retriever and time it
        start_time = time.time()
        retrieved_docs = retriever.get_relevant_documents(query, domain=domain)
        latency = (time.time() - start_time) * 1000 # in ms
        
        latencies.append(latency)
        
        # 5. Check if source document was successfully recalled
        source_art = str(source_doc.metadata.get("article_no", ""))
        source_type = source_doc.metadata.get("type", "")
        
        matched = False
        relevant_count = 0
        for doc in retrieved_docs:
            if str(doc.metadata.get("article_no", "")) == source_art and doc.metadata.get("type", "") == source_type:
                matched = True
                relevant_count += 1
                
        recall_matches.append(1 if matched else 0)
        precision_scores.append(relevant_count / len(retrieved_docs) if retrieved_docs else 0.0)
        
        if (i + 1) % 10 == 0 or (i + 1) == args.trials:
            running_recall = sum(recall_matches) / len(recall_matches) * 100
            running_precision = sum(precision_scores) / len(precision_scores) * 100
            running_latency = sum(latencies) / len(latencies)
            print(f"  Processed {i + 1}/{args.trials} trials... Running Recall: {running_recall:.1f}%, Running Precision: {running_precision:.1f}%, Running Avg Latency: {running_latency:.1f}ms")
            
    # Calculate retrieval statistics
    avg_recall = sum(recall_matches) / len(recall_matches) * 100
    avg_precision = sum(precision_scores) / len(precision_scores) * 100
    mean_lat = sum(latencies) / len(latencies)
    med_lat = get_percentile(latencies, 50)
    p90_lat = get_percentile(latencies, 90)
    p95_lat = get_percentile(latencies, 95)
    
    print("\n==========================================")
    print("RETRIEVAL STAGE MONTE CARLO STATISTICS")
    print("==========================================")
    print(f"Total Trials Sampled       : {args.trials}")
    print(f"Source Document Recall Rate: {avg_recall:.2f}%")
    print(f"Source Document Precision  : {avg_precision:.2f}%")
    print(f"Mean Retrieval Latency     : {mean_lat:.2f} ms")
    print(f"Median Retrieval Latency   : {med_lat:.2f} ms")
    print(f"90th Percentile Latency    : {p90_lat:.2f} ms")
    print(f"95th Percentile Latency    : {p95_lat:.2f} ms")
    print("==========================================")
    
    print(f"\nRunning {args.e2e} End-to-End LLM Synthesis Trials...")
    e2e_latencies = []
    
    for i in range(args.e2e):
        source_doc = random.choice(retriever.all_docs)
        query = generate_monte_carlo_query(source_doc)
        print(f"\n[E2E Trial {i+1}] Query: '{query}'")
        print(f"  Target: {source_doc.metadata.get('act_name', 'Constitution')} Section/Article {source_doc.metadata.get('article_no')}")
        
        start_time = time.time()
        response = generator.generate_rag_response(query)
        latency = time.time() - start_time
        e2e_latencies.append(latency)
        
        print(f"  Answer: {response['answer'][:200]}...")
        print(f"  Latency: {latency:.2f}s")
        
    avg_e2e_lat = sum(e2e_latencies) / len(e2e_latencies)
    print(f"\nAverage End-to-End Latency: {avg_e2e_lat:.2f}s")
    print("==========================================")

if __name__ == "__main__":
    main()
