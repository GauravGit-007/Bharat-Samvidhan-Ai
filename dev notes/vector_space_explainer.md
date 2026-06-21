# Understanding the Vector Embedding Space & RAG Process

This guide explains how our legal assistant uses vector embeddings and similarity search to retrieve and synthesize accurate legal answers.

---

## 📸 Vector Space Visualization
Here is a conceptual diagram representing how documents and queries are organized geometrically in a vector space:

![Vector Space Visualization](C:\Users\hp\.gemini\antigravity-ide\brain\f33bc7c1-e424-4737-bc86-27d6247e281f\vector_embedding_space_1781872530664.png)

---

## 1. Transforming Text to Coordinates (Embeddings)
Computers cannot read text like humans do, so we convert text into math.
* **The Embedding Model**: We use [bge-small-en-v1.5](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/retrieval/retriever.py#L8).
* **The Dimensions**: This model translates any text chunk (a section of the Constitution or the IPC) into a vector consisting of **384 numerical coordinates**. 
* **Semantic Mapping**: In this 384-dimensional space, sentences with similar *meanings* are located close to each other, even if they use completely different words (e.g., "incarceration" and "jail" will land near each other).

---

## 2. Organization of the Vector DB
The vector database (Chroma) stores all the pre-calculated coordinates of our legal documents, which form natural "clusters" based on content:

| Cluster | Content Examples | Geometrical Location |
| :--- | :--- | :--- |
| **Constitutional Rights** | Articles 14, 19, 21, 22 (freedom, equality, arrest rights) | Located in one region of the vector space. |
| **Criminal Penal Code (IPC)** | Sections 300, 302, 378, 379 (murder, theft, crimes) | Located in a separate region. |
| **User Memory / Facts** | Extracted facts (e.g., "User is a doctor", "lives in Mumbai") | Stored in a distinct user-memory collection. |

---

## 3. The Retrieval Walkthrough (An Actual Example)

Let's trace what happens when you enter this query:
> **Query:** *"What are my rights if I am arrested for theft?"*

### Step A: Embed the Query
The system sends the query to the embedding model. It returns a 384-dimensional query vector:
$$v_{\text{query}} = [0.12, -0.45, 0.08, \dots, 0.91]$$

### Step B: Compute Distances in Chroma
The Vector DB calculates the distance (typically **Cosine Similarity**) between $v_{\text{query}}$ and every document vector in the database.
* The query talks about **"arrest rights"**, so its vector lands very close to **Article 22** (Protection against arrest and detention).
* The query talks about **"theft"**, so its vector also lands close to **Section 378 & 379 IPC** (Theft and its punishment).
* Unrelated articles (e.g., Article 280 on the Finance Commission) are geometrically far away.

### Step C: Retrieve Top Matches
The database selects the nearest documents (e.g., top 5 matches):
1. **Article 22** (Distance: 0.22) - *Matches "arrest rights"*
2. **Section 378 IPC** (Distance: 0.29) - *Matches "theft"*
3. **Section 379 IPC** (Distance: 0.31) - *Matches "punishment for theft"*
4. **Article 21** (Distance: 0.38) - *Matches "life and personal liberty"*

---

## 4. The Synthesis Step (Generation)
Once the database finds the text of these top matches, it passes them directly to the LLM inside a structured [SYSTEM_PROMPT](file:///c:/github%20projects/11%20bharat%20constitution%20ml%20model/src/config/prompts.py#L10):

```markdown
[SYSTEM INSTRUCTION]
You are Bharat Samvidhan AI. Answer based ONLY on the context below. Cite articles/sections explicitly.

[CONTEXT FROM VECTOR SEARCH]
- Article 22: "No person who is arrested shall be detained in custody without..."
- Section 378 IPC: "Whoever, intending to take dishonestly any moveable property..."
- Section 379 IPC: "Whoever commits theft shall be punished with imprisonment..."

[USER QUERY]
"What are my rights if I am arrested for theft?"
```

The LLM (e.g. `llama3.2:1b`) reads this prompt, extracts the exact legal details, and generates a structured, verified legal summary citing **Article 22** and **Section 378/379** without hallucinating outside information.
