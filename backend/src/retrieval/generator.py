from langchain_community.llms import Ollama, HuggingFaceEndpoint
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from src.config.settings import settings
from src.config.prompts import SYSTEM_PROMPT, QA_PROMPT_TEMPLATE, ROUTER_PROMPT
from src.retrieval.retriever import Retriever

import urllib.request
import json
import os
import groq

def check_and_select_model(base_url: str, default_model: str) -> str:
    # 1. First, check if Ollama is even running
    tags_url = f"{base_url}/api/tags"
    try:
        req = urllib.request.Request(tags_url)
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.getcode() != 200:
                print(f"[Ollama Selector] Tags endpoint returned {response.getcode()}.")
                return default_model
            body = response.read().decode('utf-8')
            data = json.loads(body)
            models = [m.get('name') for m in data.get('models', [])]
            if not models:
                print("[Ollama Selector] No models installed in Ollama.")
                return default_model
    except Exception as e:
        print(f"[Ollama Selector] Failed to connect to Ollama tags endpoint: {e}")
        return default_model

    # 2. Helper to test if a specific model is actually functional
    def test_model(model_name: str) -> bool:
        gen_url = f"{base_url}/api/generate"
        payload = {
            "model": model_name,
            "prompt": "Hi",
            "stream": False,
            "options": {"num_predict": 1} # super fast response test
        }
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(gen_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    res_body = response.read().decode('utf-8')
                    json.loads(res_body)
                    return True
        except Exception as err:
            print(f"[Ollama Selector] Model '{model_name}' test failed: {err}")
        return False

    # 3. Test the default model first
    matching_models = []
    for m in models:
        if m == default_model or m.split(':')[0] == default_model.split(':')[0]:
            matching_models.append(m)
    
    # Try exact match or base name matches first
    for m in matching_models:
        if test_model(m):
            print(f"[Ollama Selector] Successfully verified model: {m}")
            return m
            
    if default_model not in matching_models and test_model(default_model):
        print(f"[Ollama Selector] Successfully verified default model: {default_model}")
        return default_model

    # 4. If default model fails, try other available models in tags
    print(f"[Ollama Selector] Default model '{default_model}' is not functional or not installed. Scanning alternatives...")
    for m in models:
        if m not in matching_models:
            if test_model(m):
                print(f"[Ollama Selector] Found working alternative model: {m}")
                return m

    print("[Ollama Selector] No functional models found. Proceeding with default.")
    return default_model

class Generator:
    def __init__(self):
        if settings.LLM_PROVIDER == "huggingface":
            self.llm = HuggingFaceEndpoint(
                repo_id=settings.MODEL_NAME,
                huggingfacehub_api_token=settings.HF_API_TOKEN,
                temperature=0.1,
                max_new_tokens=512,
            )
        elif settings.LLM_PROVIDER == "groq":
            # Avoid Ollama tag checking and setup entirely for Groq deployments
            self.llm = None
        else:
            # Auto-detect a working Ollama model
            working_model = check_and_select_model(settings.OLLAMA_BASE_URL, settings.MODEL_NAME)
            settings.MODEL_NAME = working_model
            
            self.llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=working_model,
                temperature=0.1,
                num_predict=512
            )
        self.retriever = Retriever()
        self.groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[Groq Init] Warning: failed to initialize Groq client: {e}")
        
        self.prompt = PromptTemplate(
            template=QA_PROMPT_TEMPLATE, 
            input_variables=["context", "user_profile_context", "chat_history_context", "query"]
        )
        self.router_prompt = PromptTemplate(
            template=ROUTER_PROMPT,
            input_variables=["query"]
        )

    def _invoke_llm(self, prompt: str, provider: str = "local") -> tuple[str, str]:
        resolved_provider = provider
        if provider == "local" and settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
            resolved_provider = "groq"

        if resolved_provider == "groq" and settings.GROQ_API_KEY:
            return self._invoke_groq(prompt)
        elif self.llm:
            return self.llm.invoke(prompt), settings.MODEL_NAME
        else:
            return (
                "⚖️ Service Temporarily Unavailable: No working LLM provider configured.",
                "error_no_provider"
            )

    def _stream_llm(self, prompt: str, provider: str = "local"):
        resolved_provider = provider
        if provider == "local" and settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
            resolved_provider = "groq"

        if resolved_provider == "groq" and settings.GROQ_API_KEY:
            yield from self._stream_groq(prompt)
        elif self.llm:
            for chunk in self.llm.stream(prompt):
                yield chunk, settings.MODEL_NAME
        else:
            yield (
                "⚖️ Service Temporarily Unavailable: No working LLM provider configured.",
                "error_no_provider"
            )

    def _invoke_groq(self, prompt: str) -> tuple[str, str]:
        if not self.groq_client:
            try:
                self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[Groq Init] Warning: failed to initialize Groq client: {e}")
        
        # Try llama-3.3-70b-versatile first
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
            )
            content = completion.choices[0].message.content
            if content:
                return content.strip(), "llama-3.3-70b-versatile"
        except Exception as e:
            print(f"[Groq Fallback] llama-3.3-70b-versatile failed: {e}. Trying llama-3.1-8b-instant...")
            
        # Try llama-3.1-8b-instant next
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
            )
            content = completion.choices[0].message.content
            if content:
                return content.strip(), "llama-3.1-8b-instant"
        except Exception as e:
            print(f"[Groq Fallback] llama-3.1-8b-instant failed: {e}.")
            
        return (
            "⚖️ Service Temporarily Unavailable: Our legal AI engines are experiencing high volume or quota limits. The system has automatically logged this incident. Please try your request again in a few moments.",
            "error_service_unavailable"
        )

    def _stream_groq(self, prompt: str):
        if not self.groq_client:
            try:
                self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[Groq Init] Warning: failed to initialize Groq client: {e}")
        
        # Try llama-3.3-70b-versatile first
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
                stream=True
            )
            
            # Read first chunk to verify availability
            iterator = iter(completion)
            first_chunk = next(iterator)
            
            yield (first_chunk.choices[0].delta.content or "", "llama-3.3-70b-versatile")
            for chunk in iterator:
                yield (chunk.choices[0].delta.content or "", "llama-3.3-70b-versatile")
            return
        except Exception as e:
            print(f"[Groq Fallback Stream] llama-3.3-70b-versatile failed: {e}. Trying llama-3.1-8b-instant...")
            
        # Try llama-3.1-8b-instant next
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
                stream=True
            )
            
            # Read first chunk to verify availability
            iterator = iter(completion)
            first_chunk = next(iterator)
            
            yield (first_chunk.choices[0].delta.content or "", "llama-3.1-8b-instant")
            for chunk in iterator:
                yield (chunk.choices[0].delta.content or "", "llama-3.1-8b-instant")
            return
        except Exception as e:
            print(f"[Groq Fallback Stream] llama-3.1-8b-instant failed: {e}.")
            
        yield (
            "⚖️ Service Temporarily Unavailable: Our legal AI engines are experiencing high volume or quota limits. The system has automatically logged this incident. Please try your request again in a few moments.",
            "error_service_unavailable"
        )

    def route_query(self, query: str) -> str:
        query_lower = query.lower()
        
        # Rule-based routing
        has_const = any(w in query_lower for w in ["constitution", "article", "fundamental right", "preamble", "amendment", "president", "parliament", "governor", "citizenship"])
        has_ipc = any(w in query_lower for w in ["ipc", "section", "punishment", "imprisonment", "jail", "fine", "crime", "murder", "theft", "defamation", "penalty", "offense", "bribe", "rebellion", "sedition"])
        
        if has_const and not has_ipc:
            return "constitution"
        elif has_ipc and not has_const:
            return "ipc"
        elif has_const and has_ipc:
            return "both"
            
        # If neither matches, let's look at the extracted citations in the query
        import re
        const_nums = re.findall(r'(?:article|art\.|art)\s*([0-9]+[a-zA-Z]*)', query_lower)
        ipc_nums = re.findall(r'(?:section|sec\.|sec)\s*([0-9]+[a-zA-Z]*)', query_lower)
        
        if const_nums and not ipc_nums:
            return "constitution"
        elif ipc_nums and not const_nums:
            return "ipc"
            
        # Default fallback: return "both" so we query both and get maximum recall, 
        # which is extremely fast and safe since similarity search takes <50ms.
        return "both"

    def generate_answer(self, query: str, provider: str = "local", focus: str = "both"):
        response = self.generate_rag_response(query, provider=provider, focus=focus)
        return response["answer"]

    def reformulate_query(self, query: str, chat_history: list, provider: str = "local") -> str:
        if not chat_history:
            return query
            
        # Fast-path check: only reformulate if query contains relative pronouns or reference words
        import re
        pronouns = ["it", "this", "that", "these", "those", "they", "he", "she", "its", "his", "her", "him", "them", "here", "there"]
        words = re.findall(r'\b\w+\b', query.lower())
        if not any(word in pronouns for word in words) and "what does" not in query.lower() and "explain" not in query.lower():
            # Already standalone, skip LLM call to save latency
            return query
            
        history_context = ""
        for msg in chat_history[-5:]:
            role_label = "Citizen" if msg["role"] == "user" else "Bharat Samvidhan AI"
            history_context += f"{role_label}: {msg['content']}\n"
            
        prompt = f"""You are a Legal Search Assistant. Given a conversation history and a follow-up query, reformulate the follow-up query into a single standalone legal search query that captures the user's intent.
Do NOT answer the question. Only output the reformulated standalone query. If no history is relevant or if the query is already standalone, output the original query.

[Conversation History]
{history_context}

Follow-up query: "{query}"
Standalone query:"""
        try:
            response, model_used = self._invoke_llm(prompt, provider=provider)
            response_clean = response.strip('"\'').strip()
            if response_clean:
                print(f"[Query Reformulator] Reformulated '{query}' -> '{response_clean}'")
                return response_clean
        except Exception as e:
            print(f"[Query Reformulator] Error: {e}")
        return query

    def _get_safe_context_and_docs(self, search_query: str, domain: str = "constitution"):
        # Retrieve relevant law documents
        docs = self.retriever.get_relevant_documents(search_query, domain=domain)
        
        # Safe context builder: limit total words in context to a reasonable size (max 1500 words for better reasoning context)
        MAX_SAFE_WORDS = 1500
        safe_docs = []
        current_word_count = 0
        for doc in docs:
            doc_words = len(doc.page_content.split())
            if current_word_count + doc_words <= MAX_SAFE_WORDS:
                safe_docs.append(doc)
                current_word_count += doc_words
            else:
                # Add only the remaining number of words from the next matching document
                remaining_words = MAX_SAFE_WORDS - current_word_count
                if remaining_words > 50:
                    truncated_content = " ".join(doc.page_content.split()[:remaining_words])
                    from langchain_core.documents import Document
                    safe_docs.append(Document(page_content=truncated_content, metadata=doc.metadata))
                    current_word_count += remaining_words
                break
            
        context = "\n\n".join([doc.page_content for doc in safe_docs])
        return context, safe_docs

    def _resolve_domain(self, focus, search_query: str):
        is_default = False
        if isinstance(focus, str):
            if focus in ["both", "all"]:
                is_default = True
        elif isinstance(focus, list):
            if len(focus) == 1 and focus[0] in ["both", "all"]:
                is_default = True
            elif not focus:
                is_default = True
        else:
            is_default = True
            
        return self.route_query(search_query) if is_default else focus

    def generate_rag_response(self, query: str, chat_history: list = None, provider: str = "local", focus = "both", session_id: str = "default"):
        import time
        start_time = time.time()
        
        # Reformulate query if chat history exists to resolve context/pronoun references
        search_query = self.reformulate_query(query, chat_history, provider=provider) if chat_history else query
        
        # Route the query (use explicit focus if set, otherwise auto-route)
        domain = self._resolve_domain(focus, search_query)
        
        # Retrieve safe relevant law documents
        ret_start = time.time()
        context, docs = self._get_safe_context_and_docs(search_query, domain=domain)
        retrieval_latency = time.time() - ret_start
        
        # Retrieve user profile facts
        user_facts = self.retriever.get_relevant_user_profile_facts(search_query, session_id=session_id)
        user_profile_context = "\n".join([f"- {fact.page_content}" for fact in user_facts]) if user_facts else "No personal profile information recorded yet."
        
        # Format chat history context for generation prompt
        history_context = ""
        if chat_history:
            for msg in chat_history[-5:]: # Context window: last 5 messages
                role_label = "Citizen" if msg["role"] == "user" else "Bharat Samvidhan AI"
                history_context += f"{role_label}: {msg['content']}\n"
        else:
            history_context = "No previous conversation history."
            
        prompt_text = self.prompt.format(
            context=context,
            user_profile_context=user_profile_context,
            chat_history_context=history_context,
            query=query
        )
        
        model_used = settings.MODEL_NAME
        try:
            gen_start = time.time()
            answer, model = self._invoke_llm(prompt_text, provider=provider)
            model_used = model
            gen_latency = time.time() - gen_start
        except Exception as e:
            gen_start = time.time()
            answer = self._fallback_synthesis(query, docs, e)
            gen_latency = time.time() - gen_start
            model_used = "fallback_synthesis"
            
        latency = time.time() - start_time
        
        return {
            "query": query,
            "answer": answer,
            "latency": round(latency, 2),
            "model_used": model_used,
            "documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                } for doc in docs
            ],
            "latency_breakdown": {
                "retrieval": round(retrieval_latency, 3),
                "generation": round(gen_latency, 3),
                "total": round(latency, 3)
            }
        }


    def generate_debug_trace(self, query: str, chat_history: list = None, provider: str = "local", focus = "both", session_id: str = "default"):
        import time
        import re
        start_time = time.time()
        
        # 1. Reformulate query if chat history exists
        ref_start = time.time()
        search_query = self.reformulate_query(query, chat_history, provider=provider) if chat_history else query
        ref_latency = time.time() - ref_start
        
        # 2. Route the query
        route_start = time.time()
        domain = self._resolve_domain(focus, search_query)
        route_latency = time.time() - route_start
        
        # 3. Retrieve relevant documents (with breakdown)
        ret_start = time.time()
        # Direct citations
        const_nums = re.findall(r'(?:article|art\.|art)\s*([0-9]+[a-zA-Z]*)', search_query, re.IGNORECASE)
        ipc_nums = re.findall(r'(?:section|sec\.|sec)\s*([0-9]+[a-zA-Z]*)', search_query, re.IGNORECASE)
        
        # Dense search (ChromaDB)
        k = settings.TOP_K
        dense_docs = []
        
        chroma_filter = None
        if domain in ["ipc", "crpc", "cpc", "evidence", "marriage", "others"]:
            if domain == "ipc":
                chroma_filter = {"type": "ipc_section"}
            elif domain == "crpc":
                chroma_filter = {"type": "crpc_section"}
            elif domain == "cpc":
                chroma_filter = {"type": "cpc_section"}
            elif domain == "evidence":
                chroma_filter = {"type": "iea_section"}
            elif domain == "marriage":
                chroma_filter = {"type": {"$in": ["hma_section", "ida_section"]}}
            elif domain == "others":
                chroma_filter = {"type": {"$in": ["mva_section", "nia_section"]}}
                
        if chroma_filter:
            dense_docs = self.retriever.ipc_db.similarity_search(search_query, k=k, filter=chroma_filter)
        elif domain == "constitution":
            dense_docs = self.retriever.constitution_db.similarity_search(search_query, k=k)
        elif domain == "both":
            dense_docs = self.retriever.constitution_db.similarity_search(search_query, k=k//2 + 1) + \
                         self.retriever.ipc_db.similarity_search(search_query, k=k//2 + 1)
            
        # Sparse search (BM25)
        sparse_docs = self.retriever.bm25_search(search_query, domain=domain, k=k)
        
        # Direct lookup citations
        citation_docs = []
        seen_const = set()
        deduped_const = [n for n in const_nums if not (n in seen_const or seen_const.add(n))]
        if domain in ["both", "constitution"]:
            for num in deduped_const:
                citation_docs.extend(self.retriever.get_by_article_no(num, domain="constitution"))
            
        seen_ipc = set()
        deduped_ipc = [n for n in ipc_nums if not (n in seen_ipc or seen_ipc.add(n))]
        for num in deduped_ipc:
            candidates = self.retriever.get_by_article_no(num, domain="ipc")
            if chroma_filter:
                allowed_types = [chroma_filter["type"]] if isinstance(chroma_filter["type"], str) else chroma_filter["type"]["$in"]
                candidates = [c for c in candidates if c.metadata.get("type") in allowed_types]
            citation_docs.extend(candidates)
            
        # Blend and deduplicate
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
                
        # Interleave standard similarity and BM25 matches
        search_candidates = []
        sim_idx, bm_idx = 0, 0
        while sim_idx < len(dense_docs) or bm_idx < len(sparse_docs):
            if sim_idx < len(dense_docs):
                doc = dense_docs[sim_idx]
                sim_idx += 1
                key = get_doc_key(doc)
                if key not in seen_keys:
                    seen_keys.add(key)
                    search_candidates.append(doc)
            if bm_idx < len(sparse_docs):
                doc = sparse_docs[bm_idx]
                bm_idx += 1
                key = get_doc_key(doc)
                if key not in seen_keys:
                    seen_keys.add(key)
                    search_candidates.append(doc)
                    
        # Apply Cross-Encoder Reranking on search candidates if enabled
        if self.retriever.use_reranker and search_candidates:
            reranked_candidates = self.retriever.rerank(query, search_candidates, top_n=k)
            blended_docs = high_priority_docs + reranked_candidates
        else:
            blended_docs = high_priority_docs + search_candidates
            
        # Adjacent fetching
        adjacent_docs = []
        for doc in blended_docs[:2]:
            doc_type = doc.metadata.get("type")
            idx = doc.metadata.get("index")
            if idx is not None:
                adj_domain = "constitution" if doc_type == "article" else "ipc"
                for adj_idx in [int(idx) - 1, int(idx) + 1]:
                    if adj_idx >= 0:
                        adjacent_docs.extend(self.retriever.get_by_index(adj_idx, domain=adj_domain, type_filter=doc_type))
                        
        final_docs = blended_docs + adjacent_docs
        seen_final = set()
        deduped_final = []
        for doc in final_docs:
            key = get_doc_key(doc)
            if key not in seen_final:
                seen_final.add(key)
                deduped_final.append(doc)
                
        # Truncate returned document count same as retriever.py
        retrieved_docs_limited = deduped_final[:max(k + 8, 15)]
        
        # Apply word limit safe context builders
        MAX_SAFE_WORDS = 1500
        safe_docs = []
        current_word_count = 0
        for doc in retrieved_docs_limited:
            doc_words = len(doc.page_content.split())
            if current_word_count + doc_words <= MAX_SAFE_WORDS:
                safe_docs.append(doc)
                current_word_count += doc_words
            else:
                remaining_words = MAX_SAFE_WORDS - current_word_count
                if remaining_words > 50:
                    truncated_content = " ".join(doc.page_content.split()[:remaining_words])
                    from langchain_core.documents import Document
                    safe_docs.append(Document(page_content=truncated_content, metadata=doc.metadata))
                    current_word_count += remaining_words
                break
                
        context = "\n\n".join([doc.page_content for doc in safe_docs])
        retrieval_latency = time.time() - ret_start
        
        # 4. Fetch user profile facts
        user_facts = self.retriever.get_relevant_user_profile_facts(search_query, session_id=session_id)
        user_profile_context = "\n".join([f"- {fact.page_content}" for fact in user_facts]) if user_facts else "No personal profile information recorded yet."
        
        # 5. Format prompt template
        history_context = "No previous conversation history."
        prompt_text = self.prompt.format(
            context=context,
            user_profile_context=user_profile_context,
            chat_history_context=history_context,
            query=query
        )
        
        # 6. LLM synthesis
        gen_start = time.time()
        model_used = settings.MODEL_NAME
        try:
            answer, model = self._invoke_llm(prompt_text, provider=provider)
            model_used = model
        except Exception as e:
            answer = self._fallback_synthesis(query, safe_docs, e)
            model_used = "fallback_synthesis"
        gen_latency = time.time() - gen_start
        
        total_latency = time.time() - start_time
        
        return {
            "query": query,
            "reformulated_query": search_query,
            "domain": domain,
            "model_used": model_used,
            "user_profile_facts": [fact.page_content for fact in user_facts],
            "dense_docs": [{"content": d.page_content, "metadata": d.metadata} for d in dense_docs],
            "sparse_docs": [{"content": d.page_content, "metadata": d.metadata} for d in sparse_docs],
            "blended_docs": [{"content": d.page_content, "metadata": d.metadata} for d in blended_docs],
            "adjacent_docs": [{"content": d.page_content, "metadata": d.metadata} for d in adjacent_docs],
            "final_docs": [{"content": d.page_content, "metadata": d.metadata} for d in safe_docs],
            "raw_prompt": prompt_text,
            "answer": answer,
            "latency_breakdown": {
                "reformulation": round(ref_latency, 3),
                "routing": round(route_latency, 3),
                "retrieval": round(retrieval_latency, 3),
                "generation": round(gen_latency, 3),
                "total": round(total_latency, 3)
            }
        }

    def consolidate_and_save_fact(self, new_fact: str, provider: str = "local", session_id: str = "default"):
        existing_docs = self.retriever.get_all_user_profile_facts(session_id=session_id)
        if not existing_docs:
            self.retriever.add_user_profile_fact(new_fact, session_id=session_id)
            return
            
        existing_facts_formatted = ""
        for i, doc in enumerate(existing_docs):
            existing_facts_formatted += f"{i}: \"{doc.page_content}\"\n"
            
        prompt = f"""You are a User Memory Consolidation Assistant. 
We have a database of facts about the user. A new fact is being added.
Your task is to identify if the new fact contradicts, replaces, or renders obsolete any of the existing facts.

[Existing Facts]
{existing_facts_formatted}

[New Fact]
"{new_fact}"

Output a JSON object in this exact format:
{{
  "outdated_fact_indices": [list of integers representing indices of outdated/contradicted facts in the existing list to be deleted],
  "reason": "brief reason for the change"
}}

If none of the existing facts are contradicted or outdated, output:
{{
  "outdated_fact_indices": [],
  "reason": "No contradictions."
}}

JSON:"""
        try:
            response, model_used = self._invoke_llm(prompt, provider=provider)
            # Extract JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx != -1:
                data = json.loads(response[start_idx:end_idx])
                outdated_indices = data.get("outdated_fact_indices", [])
                
                # Delete outdated facts
                ids_to_delete = []
                for idx in outdated_indices:
                    if 0 <= idx < len(existing_docs):
                        doc_id = existing_docs[idx].metadata.get("id")
                        if doc_id:
                            ids_to_delete.append(doc_id)
                            
                if ids_to_delete:
                    print(f"[Memory RAG] Deleting outdated/contradictory facts: {ids_to_delete} due to: {data.get('reason')}")
                    self.retriever.user_profile_db.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"[Memory RAG] Error during memory consolidation: {e}")
            
        # Finally, save the new fact
        self.retriever.add_user_profile_fact(new_fact, session_id=session_id)

    def extract_and_save_user_data(self, query: str, provider: str = "local", session_id: str = "default"):
        # Pre-filter user data phrases to avoid extra LLM latency for standard legal queries
        personal_keywords = ["my name", "i am a", "i live in", "i work as", "my age", "old from", "from city", "scenario", "situation", "name is", "i am from"]
        query_lower = query.lower()
        if not any(kw in query_lower for kw in personal_keywords):
            return
            
        prompt = f"""Analyze the user's input query. If the user mentions any personal information about themselves (such as their name, age, location, occupation, or a specific personal background scenario they are experiencing), extract ONLY the facts as a concise list of declarations, with each fact on a new line starting with a dash.
        Do NOT write any notes, warnings, introductions, explanations, or meta-comments. Output ONLY the facts or the word NONE.

        Input query: "{query}"

        Extracted Facts:"""
        try:
            response, model_used = self._invoke_llm(prompt, provider=provider)
            if response.upper() != "NONE" and "NONE" not in response:
                facts = [line.strip("- *").strip() for line in response.split("\n") if line.strip()]
                for fact in facts:
                    if not fact:
                        continue
                    fact_lower = fact.lower()
                    # Filter out meta-notes or empty facts
                    if "note:" in fact_lower or "the query" in fact_lower or "the user is" in fact_lower or "mention" in fact_lower or "ignore" in fact_lower:
                        continue
                    print(f"[Memory RAG] Consolidating and saving user profile fact: {fact}")
                    self.consolidate_and_save_fact(fact, provider=provider, session_id=session_id)
        except Exception as e:
            print(f"[Memory RAG] Error extracting user data: {e}")

    def _fallback_synthesis(self, query: str, docs: list, original_error: Exception) -> str:
        print(f"Ollama connection unavailable ({original_error}). Running Fallback Legal Synthesis...")
        if not docs:
            return "No relevant constitutional articles or IPC sections were found matching your query."
            
        primary_doc = docs[0]
        doc_type = "IPC Section" if primary_doc.metadata.get("type") == "ipc_section" else "Constitution Article"
        ref_no = primary_doc.metadata.get("article_no") or primary_doc.metadata.get("section_no") or "N/A"
        
        summary = f"### ⚖️ Juris AI Fallback Legal Reference Synthesis\n\n"
        summary += f"*Note: The local Ollama server is offline or unreachable. The system has automatically extracted and structured the most relevant legal citations directly from the vector store for your reference.*\n\n"
        summary += f"Based on the semantic matching in the **{doc_type}** collection, the most relevant reference found is **{doc_type} {ref_no}**:\n\n"
        summary += f"> {primary_doc.page_content}\n\n"
        
        if len(docs) > 1:
            summary += "### Supporting Citations:\n"
            for doc in docs[1:3]:
                s_type = "IPC Section" if doc.metadata.get("type") == "ipc_section" else "Constitution Article"
                s_ref = doc.metadata.get("article_no") or doc.metadata.get("section_no") or "N/A"
                summary += f"- **{s_type} {s_ref}**: {doc.page_content[:180]}...\n"
                
        return summary

    def generate_rag_stream(self, query: str, chat_history: list = None, provider: str = "local", focus = "both", session_id: str = "default"):
        import time
        start_time = time.time()
        
        # Reformulate query if chat history exists to resolve context/pronoun references
        search_query = self.reformulate_query(query, chat_history, provider=provider) if chat_history else query
        
        # Route the query (use explicit focus if set, otherwise auto-route)
        domain = self._resolve_domain(focus, search_query)
        
        # Retrieve safe relevant law documents
        context, docs = self._get_safe_context_and_docs(search_query, domain=domain)
        
        # Retrieve user profile facts
        user_facts = self.retriever.get_relevant_user_profile_facts(search_query, session_id=session_id)
        user_profile_context = "\n".join([f"- {fact.page_content}" for fact in user_facts]) if user_facts else "No personal profile information recorded yet."
        
        # Format chat history context for generation prompt
        history_context = ""
        if chat_history:
            for msg in chat_history[-5:]: # Context window: last 5 messages
                role_label = "Citizen" if msg["role"] == "user" else "Bharat Samvidhan AI"
                history_context += f"{role_label}: {msg['content']}\n"
        else:
            history_context = "No previous conversation history."
            
        prompt_text = self.prompt.format(
            context=context,
            user_profile_context=user_profile_context,
            chat_history_context=history_context,
            query=query
        )
        
        # Construct and yield the retrieved documents metadata immediately so the UI can render them
        yield {
            "type": "documents",
            "documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                } for doc in docs
            ]
        }
        
        model_used = settings.MODEL_NAME
        try:
            # Stream response chunks from the LLM in real-time
            for chunk, model in self._stream_llm(prompt_text, provider=provider):
                if model:
                    model_used = model
                yield {
                    "type": "token",
                    "content": chunk
                }
        except Exception as e:
            # Fallback output if LLM stream fails
            fallback_answer = self._fallback_synthesis(query, docs, e)
            yield {
                "type": "token",
                "content": fallback_answer
            }
            model_used = "fallback_synthesis"
            
        latency = time.time() - start_time
        yield {
            "type": "done",
            "latency": round(latency, 2),
            "model_used": model_used
        }

    def generate_with_custom_prompt(self, query: str, session_id: str = "default"):
        # Using the more detailed system prompt
        context, docs = self._get_safe_context_and_docs(query)
        
        user_facts = self.retriever.get_relevant_user_profile_facts(query, session_id=session_id)
        user_profile_context = "\n".join([f"- {fact.page_content}" for fact in user_facts]) if user_facts else "No personal profile information recorded yet."
        
        full_prompt = SYSTEM_PROMPT.format(
            context=context,
            user_profile_context=user_profile_context,
            chat_history_context="No history.",
            query=query
        )
        return self.llm.invoke(full_prompt)

if __name__ == "__main__":
    generator = Generator()
    query = "What is Article 21?"
    print(f"Query: {query}")
    answer = generator.generate_answer(query)
    print(f"\nAnswer:\n{answer}")
