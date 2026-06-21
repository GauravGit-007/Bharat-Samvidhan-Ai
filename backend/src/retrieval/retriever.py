import os
import re
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from src.config.settings import settings

import threading

_reranker_instance = None
_reranker_lock = threading.Lock()

def get_reranker_instance(model_name: str):
    global _reranker_instance
    if _reranker_instance is None:
        with _reranker_lock:
            if _reranker_instance is None:
                from sentence_transformers import CrossEncoder
                import inspect
                print(f"[Reranker] Loading CrossEncoder: {model_name} on CPU...")
                
                # Set environment variables to route cache downloads for older versions
                os.environ["HF_HOME"] = os.path.abspath("./data/models")
                os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.abspath("./data/models")
                
                sig = inspect.signature(CrossEncoder.__init__)
                kwargs = {
                    "device": "cpu",
                    "default_activation_function": None
                }
                if "cache_folder" in sig.parameters:
                    kwargs["cache_folder"] = './data/models'
                
                _reranker_instance = CrossEncoder(model_name, **kwargs)
    return _reranker_instance

class Retriever:
    def __init__(self):
        # 1. Optimize SQLite journal and lock modes for high concurrency
        self._optimize_sqlite()
        
        self.embeddings = FastEmbedEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            cache_dir='./data/models'
        )
        # Constitution Vector DB
        self.constitution_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embeddings,
            collection_name=settings.COLLECTION_NAME
        )
        # IPC (and other statutes) Vector DB
        self.ipc_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embeddings,
            collection_name=settings.IPC_COLLECTION_NAME
        )
        # User Profile Vector DB (Memory RAG)
        self.user_profile_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embeddings,
            collection_name="user_profile"
        )
        
        # Initialize BM25 index on startup (lazily loads if DB is not ready yet)
        self.bm25 = None
        self.all_docs = []
        self._initialize_bm25()
        
        # Initialize dynamic concept map
        self.concept_map = self._load_concept_map()
        
        # Initialize reranker config
        self.use_reranker = settings.USE_RERANKER
        self.reranker_model_name = settings.RERANK_MODEL
        self.reranker = None

    def _optimize_sqlite(self):
        try:
            import sqlite3
            db_file = os.path.join(settings.CHROMA_DB_PATH, "chroma.sqlite3")
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                # Fetch output to verify WAL mode
                cursor.execute("PRAGMA journal_mode;")
                res = cursor.fetchone()
                print(f"[SQLite Optimizer] SQLite WAL journal mode verified: {res[0] if res else 'WAL'}")
                conn.close()
        except Exception as e:
            print(f"[SQLite Optimizer] Error optimizing SQLite: {e}")

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _initialize_bm25(self):
        try:
            import time
            start = time.time()
            
            # Fetch all from constitution
            const_res = self.constitution_db.get()
            const_docs = []
            if const_res and const_res.get("documents"):
                from langchain_core.documents import Document
                for text, metadata in zip(const_res["documents"], const_res["metadatas"]):
                    const_docs.append(Document(page_content=text, metadata=metadata))
            
            # Fetch all from ipc
            ipc_res = self.ipc_db.get()
            ipc_docs = []
            if ipc_res and ipc_res.get("documents"):
                from langchain_core.documents import Document
                for text, metadata in zip(ipc_res["documents"], ipc_res["metadatas"]):
                    ipc_docs.append(Document(page_content=text, metadata=metadata))
            
            self.all_docs = const_docs + ipc_docs
            if not self.all_docs:
                print("[BM25] No documents found in database yet. BM25 is uninitialized.")
                return
                
            from rank_bm25 import BM25Okapi
            tokenized_corpus = [self._tokenize(doc.page_content) for doc in self.all_docs]
            self.bm25 = BM25Okapi(tokenized_corpus)
            print(f"[BM25] Initialized BM25 index with {len(self.all_docs)} documents in {time.time() - start:.3f}s")
        except Exception as e:
            print(f"[BM25] Failed to initialize BM25: {e}")

    def _load_concept_map(self) -> dict:
        import json
        config_path = os.path.join("data", "processed", "concept_map.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                default_map = {
                    "constitution": {
                        "practice_practise_profession_occupation_trade_business": {
                            "keywords": ["practice", "practise", "profession", "occupation", "trade", "business"],
                            "citations": ["19"]
                        },
                        "rebellion_overthrow_revolution": {
                            "keywords": ["rebellion", "overthrow", "revolution"],
                            "citations": ["19"]
                        },
                        "education_school_children_compulsory": {
                            "keywords": ["education", "school", "children", "compulsory"],
                            "citations": ["21A", "45", "30"]
                        },
                        "arrest_custody_detention_warrant_grounds": {
                            "keywords": ["arrest", "custody", "detention", "warrant", "grounds"],
                            "citations": ["22"]
                        },
                        "life_personal_liberty_deprived": {
                            "keywords": ["life", "personal liberty", "deprived"],
                            "citations": ["21"]
                        },
                        "emergency_emergency_proclamation_suspend_war_external_aggression": {
                            "keywords": ["emergency", "emergency proclamation", "suspend", "war", "external aggression"],
                            "citations": ["359", "358", "352"]
                        },
                        "equality_discrimination_equal_opportunity_untouchability": {
                            "keywords": ["equality", "discrimination", "equal opportunity", "untouchability"],
                            "citations": ["14", "15", "16", "17"]
                        },
                        "religion_religious_worship_conscience": {
                            "keywords": ["religion", "religious", "worship", "conscience"],
                            "citations": ["25", "26", "27", "28"]
                        },
                        "self-incrimination_incriminate_double_jeopardy_prosecuted_punished": {
                            "keywords": ["self-incrimination", "incriminate", "double jeopardy", "prosecuted and punished"],
                            "citations": ["20"]
                        },
                        "taxation_tax_levy_taxes_collected": {
                            "keywords": ["taxation", "tax", "levy", "taxes", "collected"],
                            "citations": ["265", "268", "269", "270"]
                        },
                        "finance_commission_recommendations": {
                            "keywords": ["finance commission", "recommendations"],
                            "citations": ["280", "281"]
                        },
                        "elections_voter_electoral_franchise_commission": {
                            "keywords": ["elections", "voter", "electoral", "franchise", "commission"],
                            "citations": ["324", "325", "326", "327"]
                        }
                    },
                    "ipc": {
                        "theft_steal_bicycle_stolen_property": {
                            "keywords": ["theft", "steal", "bicycle", "stolen", "property"],
                            "citations": ["378", "379"]
                        },
                        "murder_kill_provocation_provoke_death": {
                            "keywords": ["murder", "kill", "provocation", "provoke", "death"],
                            "citations": ["300", "302", "304"]
                        },
                        "defam_public_slander_libel": {
                            "keywords": ["defam", "public", "slander", "libel"],
                            "citations": ["499", "500"]
                        },
                        "bribe_bribing_corruption_official_gratification": {
                            "keywords": ["bribe", "bribing", "corruption", "official", "gratification"],
                            "citations": ["171B", "169"]
                        },
                        "rebellion_overthrow_sedition_rebel_waging_war": {
                            "keywords": ["rebellion", "overthrow", "sedition", "rebel", "waging war"],
                            "citations": ["121", "121A", "122", "124A"]
                        }
                    }
                }
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(default_map, f, indent=4)
                return default_map
        except Exception as e:
            print(f"[Retriever] Error loading concept map JSON: {e}")
            return {}

    def rerank(self, query: str, docs: list, top_n: int = 5) -> list:
        if not docs:
            return []
        import time
        start_wait = time.time()
        try:
            reranker = get_reranker_instance(self.reranker_model_name)
            
            pairs = [[query, doc.page_content] for doc in docs]
            
            # Serialize inference to prevent massive RAM spikes
            with _reranker_lock:
                wait_time = time.time() - start_wait
                scores = reranker.predict(pairs)
            
            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            for doc, score in scored_docs:
                doc.metadata["rerank_score"] = float(score)
                # Attach wait time to the top doc to pass it back up
                doc.metadata["reranker_lock_wait"] = wait_time
                
            return [doc for doc, score in scored_docs][:top_n]
        except Exception as e:
            print(f"[Reranker Error] {e}")
            return docs[:top_n]


    def bm25_search(self, query: str, domain = "both", k: int = 5) -> list:
        # Lazy initialization if not yet set up
        if not self.bm25 or not self.all_docs:
            self._initialize_bm25()
        if not self.bm25 or not self.all_docs:
            return []
            
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Sort indices by score
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize domain to list
        if isinstance(domain, str):
            domain_list = [domain]
        else:
            domain_list = list(domain)
            
        allowed_types = []
        is_all = "all" in domain_list or "both" in domain_list or not domain_list
        
        if not is_all:
            for d in domain_list:
                if d == "constitution":
                    allowed_types.append("article")
                elif d == "ipc":
                    allowed_types.append("ipc_section")
                elif d == "crpc":
                    allowed_types.append("crpc_section")
                elif d == "cpc":
                    allowed_types.append("cpc_section")
                elif d == "evidence":
                    allowed_types.append("iea_section")
                elif d == "marriage":
                    allowed_types.extend(["hma_section", "ida_section"])
                elif d == "others":
                    allowed_types.extend(["mva_section", "nia_section"])
        
        results = []
        for idx, score in indexed_scores:
            if len(results) >= k:
                break
            if score <= 0:
                continue
                
            doc = self.all_docs[idx]
            doc_type = doc.metadata.get("type", "")
            
            # Domain filtering
            if not is_all and doc_type not in allowed_types:
                continue
            if is_all and doc_type == "user_data": # ignore profile logs in search results
                continue
                
            results.append(doc)
        return results

    def add_user_profile_fact(self, fact: str):
        try:
            self.user_profile_db.add_texts(texts=[fact], metadatas=[{"type": "user_data"}])
        except Exception as e:
            print(f"Error adding user profile fact: {e}")

    def get_relevant_user_profile_facts(self, query: str, k: int = 3):
        try:
            if self.user_profile_db._collection.count() == 0:
                return []
            return self.user_profile_db.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error reading user profile facts: {e}")
            return []

    def get_all_user_profile_facts(self):
        try:
            if self.user_profile_db._collection.count() == 0:
                return []
            res = self.user_profile_db.get()
            docs = []
            if res and res.get("documents"):
                from langchain_core.documents import Document
                for text, metadata, doc_id in zip(res["documents"], res["metadatas"], res["ids"]):
                    meta = metadata.copy()
                    meta["id"] = doc_id
                    docs.append(Document(page_content=text, metadata=meta))
            return docs
        except Exception as e:
            print(f"Error getting all user profile facts: {e}")
            return []

    def get_by_article_no(self, number: str, domain: str = "constitution"):
        try:
            db = self.ipc_db if domain == "ipc" else self.constitution_db
            res = db.get(where={"article_no": str(number)})
            docs = []
            if res and res.get("documents"):
                from langchain_core.documents import Document
                for text, metadata in zip(res["documents"], res["metadatas"]):
                    docs.append(Document(page_content=text, metadata=metadata))
            return docs
        except Exception as e:
            print(f"Error in get_by_article_no: {e}")
            return []

    def get_by_index(self, index: int, domain: str = "constitution", type_filter: str = None):
        try:
            db = self.ipc_db if domain == "ipc" else self.constitution_db
            if type_filter:
                where_clause = {
                    "$and": [
                        {"index": int(index)},
                        {"type": type_filter}
                    ]
                }
            else:
                where_clause = {"index": int(index)}
            res = db.get(where=where_clause)
            docs = []
            if res and res.get("documents"):
                from langchain_core.documents import Document
                for text, metadata in zip(res["documents"], res["metadatas"]):
                    docs.append(Document(page_content=text, metadata=metadata))
            return docs
        except Exception as e:
            print(f"Error in get_by_index: {e}")
            return []

    def get_relevant_documents(self, query: str, domain = "constitution", k: int = None):
        if k is None:
            k = settings.TOP_K
            
        # 1. Extract explicit article/section citations
        const_nums = re.findall(r'(?:article|art\.|art)\s*([0-9]+[a-zA-Z]*)', query, re.IGNORECASE)
        ipc_nums = re.findall(r'(?:section|sec\.|sec)\s*([0-9]+[a-zA-Z]*)', query, re.IGNORECASE)
        
        # 2. Concept-based synonym/keyword boosting
        concept_nums_const = []
        concept_nums_ipc = []
        query_lower = query.lower()
        
        const_mapping = self.concept_map.get("constitution", {})
        for key, entry in const_mapping.items():
            keywords = entry.get("keywords", [])
            citations = entry.get("citations", [])
            if any(kw in query_lower for kw in keywords):
                concept_nums_const.extend(citations)
                
        ipc_mapping = self.concept_map.get("ipc", {})
        for key, entry in ipc_mapping.items():
            keywords = entry.get("keywords", [])
            citations = entry.get("citations", [])
            if any(kw in query_lower for kw in keywords):
                concept_nums_ipc.extend(citations)
                
        # Determine if we should query constitution_db and/or ipc_db
        query_const = False
        query_ipc = False
        
        # Statutory type filters to combine using $in
        ipc_types = []
        
        # Normalize domain to list
        if isinstance(domain, str):
            domain_list = [domain]
        else:
            domain_list = list(domain)
            
        if "all" in domain_list or "both" in domain_list or not domain_list:
            query_const = True
            query_ipc = True
            chroma_filter = None
        else:
            if "constitution" in domain_list:
                query_const = True
            
            # Check statutory types
            for d in domain_list:
                if d == "ipc":
                    ipc_types.append("ipc_section")
                elif d == "crpc":
                    ipc_types.append("crpc_section")
                elif d == "cpc":
                    ipc_types.append("cpc_section")
                elif d == "evidence":
                    ipc_types.append("iea_section")
                elif d == "marriage":
                    ipc_types.extend(["hma_section", "ida_section"])
                elif d == "others":
                    ipc_types.extend(["mva_section", "nia_section"])
                    
            if ipc_types:
                query_ipc = True
                if len(ipc_types) == 1:
                    chroma_filter = {"type": ipc_types[0]}
                else:
                    chroma_filter = {"type": {"$in": ipc_types}}
            else:
                chroma_filter = None

        # Resolve all targeted lookup numbers (preserving priority order by avoiding set random hashing)
        citation_docs = []
        seen_const = set()
        deduped_const = [n for n in (const_nums + concept_nums_const) if not (n in seen_const or seen_const.add(n))]
        if query_const:
            for num in deduped_const:
                citation_docs.extend(self.get_by_article_no(num, domain="constitution"))
            
        seen_ipc = set()
        deduped_ipc = [n for n in (ipc_nums + concept_nums_ipc) if not (n in seen_ipc or seen_ipc.add(n))]
        if query_ipc:
            for num in deduped_ipc:
                candidates = self.get_by_article_no(num, domain="ipc")
                if chroma_filter:
                    allowed_types = [chroma_filter["type"]] if isinstance(chroma_filter["type"], str) else chroma_filter["type"]["$in"]
                    candidates = [c for c in candidates if c.metadata.get("type") in allowed_types]
                citation_docs.extend(candidates)
            
        # 3. Standard similarity search (Vector DB)
        similarity_docs = []
        if query_const and query_ipc:
            import concurrent.futures
            try:
                # Pre-compute the query embedding once to avoid computing it twice
                query_embedding = self.embeddings.embed_query(query)
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future_const = executor.submit(self.constitution_db.similarity_search_by_vector, query_embedding, k=k//2 + 1)
                    future_ipc = executor.submit(self.ipc_db.similarity_search_by_vector, query_embedding, k=k//2 + 1, filter=chroma_filter)
                    docs_const = future_const.result()
                    docs_ipc = future_ipc.result()
                similarity_docs = docs_const + docs_ipc
            except Exception as e:
                print(f"Error in concurrent similarity search: {e}")
                # Fallback to sequential standard search on error
                docs_const = self.constitution_db.similarity_search(query, k=k//2 + 1)
                docs_ipc = self.ipc_db.similarity_search(query, k=k//2 + 1, filter=chroma_filter)
                similarity_docs = docs_const + docs_ipc
        elif query_const:
            similarity_docs = self.constitution_db.similarity_search(query, k=k)
        elif query_ipc:
            similarity_docs = self.ipc_db.similarity_search(query, k=k, filter=chroma_filter)
            
        # 4. Sparse search (BM25)
        bm25_docs = self.bm25_search(query, domain=domain, k=k)
        
        # 5. Hybrid Blending (Interleaving citations, standard similarity, and BM25)
        high_priority_docs = []
        seen_keys = set()
        
        def get_doc_key(doc):
            return (doc.metadata.get("type"), str(doc.metadata.get("article_no")), doc.page_content[:100])
            
        # Direct citations first
        for doc in citation_docs:
            key = get_doc_key(doc)
            if key not in seen_keys:
                seen_keys.add(key)
                high_priority_docs.append(doc)
                
        # Interleave similarity and BM25 matches
        search_candidates = []
        sim_idx, bm_idx = 0, 0
        while sim_idx < len(similarity_docs) or bm_idx < len(bm25_docs):
            if sim_idx < len(similarity_docs):
                doc = similarity_docs[sim_idx]
                sim_idx += 1
                key = get_doc_key(doc)
                if key not in seen_keys:
                    seen_keys.add(key)
                    search_candidates.append(doc)
            if bm_idx < len(bm25_docs):
                doc = bm25_docs[bm_idx]
                bm_idx += 1
                key = get_doc_key(doc)
                if key not in seen_keys:
                    seen_keys.add(key)
                    search_candidates.append(doc)
                    
        # Apply Cross-Encoder Reranking on search candidates if enabled
        if self.use_reranker and search_candidates:
            # Rerank search candidates and take top K
            reranked_candidates = self.rerank(query, search_candidates, top_n=k)
            combined_docs = high_priority_docs + reranked_candidates
        else:
            combined_docs = high_priority_docs + search_candidates
        
        # 6. Contextual adjacent fetching (by act type specific database index)
        adjacent_docs = []
        for doc in combined_docs[:2]:
            doc_type = doc.metadata.get("type")
            idx = doc.metadata.get("index")
            if idx is not None:
                adj_domain = "constitution" if doc_type == "article" else "ipc"
                # Query index - 1 and index + 1
                for adj_idx in [int(idx) - 1, int(idx) + 1]:
                    if adj_idx >= 0:
                        adjacent_docs.extend(self.get_by_index(adj_idx, domain=adj_domain, type_filter=doc_type))
                        
        # Combine all and final deduplication
        final_docs = combined_docs + adjacent_docs
        
        seen = set()
        deduped_docs = []
        for doc in final_docs:
            key = get_doc_key(doc)
            if key not in seen:
                seen.add(key)
                deduped_docs.append(doc)
                
        # Limit to reasonable count to ensure adjacent sections are preserved
        return deduped_docs[:max(k + 8, 15)]

if __name__ == "__main__":
    retriever = Retriever()
    query = "What are the fundamental rights in India?"
    docs = retriever.get_relevant_documents(query)
    print(f"Found {len(docs)} relevant documents.")
    for i, doc in enumerate(docs):
        print(f"\nResult {i+1}:")
        print(f"Article: {doc.metadata.get('article_no', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")
