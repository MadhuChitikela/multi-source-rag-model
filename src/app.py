import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from pinecone import Pinecone
from groq import Groq

# Load environment variables
load_dotenv()

# Verify environment variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "multiragsystem")

if not PINECONE_API_KEY:
    print("[ERROR] PINECONE_API_KEY not found in environment. Please check your .env file.")
if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY not found in environment. Please check your .env file.")

app = FastAPI(title="Multi-Source RAG API", description="FastAPI Backend for Multi-Source Finance & E-Commerce RAG")

# Enable CORS for flexible development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pinecone client setup
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
except Exception as e:
    print(f"[ERROR] Failed to initialize Pinecone: {e}")
    index = None

# Groq client setup
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"[ERROR] Failed to initialize Groq client: {e}")
    groq_client = None

# Request/Response schemas
class QueryRequest(BaseModel):
    question: str
    namespaces: List[str] = ["products", "stocks", "deals", "documents", "news"]

class Source(BaseModel):
    text: str
    score: float
    namespace: str
    metadata: dict

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

@app.get("/health")
def health():
    if not PINECONE_API_KEY or not GROQ_API_KEY:
        return {"status": "degraded", "error": "Missing API keys in environment"}
    if not index:
        return {"status": "degraded", "error": "Pinecone index not initialized"}
    if not groq_client:
        return {"status": "degraded", "error": "Groq client not initialized"}
    return {"status": "ok"}

# Serve HTML at root
@app.get("/", response_class=HTMLResponse)
def get_root():
    static_file_path = os.path.join("src", "static", "index.html")
    if not os.path.exists(static_file_path):
        raise HTTPException(status_code=404, detail="Frontend HTML file not found.")
    with open(static_file_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    if not index:
        raise HTTPException(status_code=500, detail="Pinecone index is not initialized.")
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq LLM client is not initialized.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not req.namespaces:
        raise HTTPException(status_code=400, detail="At least one namespace must be selected.")

    # 1. Retrieve from each selected namespace using Pinecone integrated search
    all_chunks = []
    for ns in req.namespaces:
        try:
            # We must use index.search() for server-side embedding generation
            resp = index.search(
                namespace=ns,
                query={
                    "inputs": {
                        "text": req.question
                    },
                    "top_k": 5
                }
            )
            result = resp.get('result', {})
            hits = result.get('hits', [])
            for hit in hits:
                fields = hit.get('fields', {})
                all_chunks.append({
                    "text": fields.get('text', ''),
                    "score": hit.get('_score', 0.0),
                    "namespace": ns,
                    "metadata": fields
                })
        except Exception as e:
            print(f"[WARNING] Error querying namespace '{ns}': {e}")

    # Sort matches from all namespaces by similarity score descending
    all_chunks.sort(key=lambda x: x['score'], reverse=True)
    top_chunks = all_chunks[:8]  # Retrieve top 8 context chunks across namespaces

    if not top_chunks:
        return QueryResponse(
            answer="No relevant information found in the selected sources. Please adjust your namespace filters or question.",
            sources=[]
        )

    # 2. Build context with clear indexing to allow proper UI citation linking
    context_blocks = []
    for idx, chunk in enumerate(top_chunks):
        meta_items = [f"{k}={v}" for k, v in chunk["metadata"].items() if k != "text"]
        meta_str = ", ".join(meta_items)
        context_blocks.append(
            f"Source [{idx+1}] (Namespace: {chunk['namespace']}, Metadata: {meta_str})\n"
            f"Content:\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    # 3. Create instructions for the LLM
    prompt = f"""You are a helpful and precise financial and e-commerce research assistant.
Answer the user's question based ONLY on the provided context sources. 
If the context does not contain enough information to answer the question, state clearly that you do not know.

IMPORTANT:
- For every fact or statement you make in your answer, you must cite the corresponding source index in square brackets, such as [1], [2], etc.
- Do not make up source indices. Use only the indices provided in the context.
- Keep the answer concise and highly structured.

Context:
{context}

Question: {req.question}

Answer:"""

    # 4. Generate completion via Groq (with fallback models if needed)
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.3-70b-specdec", "llama3-70b-8192"]
    completion = None
    last_error = None

    for model_name in models_to_try:
        try:
            completion = groq_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            break  # Success, exit loop
        except Exception as e:
            print(f"[WARNING] Model {model_name} failed: {e}")
            last_error = e

    if not completion:
        raise HTTPException(status_code=500, detail=f"LLM completion failed: {last_error}")

    answer = completion.choices[0].message.content

    # 5. Return response
    return QueryResponse(
        answer=answer,
        sources=[Source(**chunk) for chunk in top_chunks]
    )

# Mount static folder for CSS, JS, assets (if any)
app.mount("/static", StaticFiles(directory=os.path.join("src", "static")), name="static")
