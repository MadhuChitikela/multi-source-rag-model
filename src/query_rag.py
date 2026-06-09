import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load dotenv to read environment variables
load_dotenv()

# Check credentials
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "multiragsystem")

if not PINECONE_API_KEY:
    print("[ERROR] PINECONE_API_KEY not found in environment. Please set it in your .env file.")
    sys.exit(1)

if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY not found in environment. Please set it in your .env file.")
    sys.exit(1)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Target namespaces to search
NAMESPACES = ["products", "stocks", "deals", "documents", "news"]
TOP_K_PER_NAMESPACE = 3

# Initialize ChatGroq LLM
llm = ChatGroq(
    model="llama-3.3-70b-specdec",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

prompt = PromptTemplate(
    template="""You are a helpful assistant. Answer the question based ONLY on the provided context.
If the answer is not contained in the context, say "I don't know". Do not attempt to make up an answer.

Context:
{context}

Question: {question}

Answer with precise citations in parentheses like (Source: namespace, field=value) based on the metadata of the context chunks you used.""",
    input_variables=["context", "question"]
)

chain = LLMChain(llm=llm, prompt=prompt)

def query_all_namespaces(question):
    all_chunks = []
    for ns in NAMESPACES:
        try:
            # Query Pinecone using index.search (server-side integrated embeddings)
            resp = index.search(
                namespace=ns,
                query={
                    "inputs": {
                        "text": question
                    },
                    "top_k": TOP_K_PER_NAMESPACE
                }
            )
            for match in resp.get('matches', []):
                metadata = match.get('metadata', {})
                all_chunks.append({
                    "text": metadata.get('text', ''),
                    "score": match.get('score', 0.0),
                    "namespace": ns,
                    "metadata": metadata
                })
        except Exception as e:
            print(f"[WARNING] Failed to query namespace '{ns}': {e}")
            
    if not all_chunks:
        return "I don't know (no matching vectors found).", []
        
    # Sort all results by similarity score descending
    all_chunks.sort(key=lambda x: x['score'], reverse=True)
    
    # Take top 6 chunks overall
    top_chunks = all_chunks[:6]
    
    # Construct context string
    context_blocks = []
    for idx, c in enumerate(top_chunks):
        # Format metadata for LLM citation reference
        meta_str = ", ".join([f"{k}={v}" for k, v in c["metadata"].items() if k != "text"])
        context_blocks.append(f"Chunk {idx+1} [Namespace: {c['namespace']}] (Metadata: {meta_str})\nContent:\n{c['text']}")
        
    context = "\n\n---\n\n".join(context_blocks)
    
    # Run chain
    answer = chain.run(context=context, question=question)
    return answer, top_chunks

if __name__ == "__main__":
    print("============================================================")
    print("🧠 MULTI-SOURCE RAG QUERY CLI ACTIVE (Type 'exit' to quit)")
    print("============================================================")
    
    while True:
        try:
            q = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
            
        if not q:
            continue
            
        if q.lower() == "exit":
            break
            
        print("\nSearching Pinecone index...")
        answer, sources = query_all_namespaces(q)
        
        print("\n" + "="*60)
        print("Answer:", answer)
        print("\nSources:")
        if sources:
            for idx, src in enumerate(sources):
                meta_summary = ", ".join([f"{k}: {v}" for k, v in src['metadata'].items() if k not in ('text', 'source_type', 'source_name')][:3])
                print(f"  [{idx+1}] Namespace '{src['namespace']}' (score {src['score']:.3f}) | {meta_summary}")
        else:
            print("  No sources found.")
        print("="*60)
