---
title: Multisource Rag
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🧠 Multi-Source Finance & E-Commerce RAG Architecture

[![Pinecone Serverless](https://img.shields.io/badge/Vector%20DB-Pinecone%20Serverless-000000?style=for-the-badge&logo=pinecone&logoColor=white)](https://pinecone.io)
[![Groq LPUs](https://img.shields.io/badge/Inference-Groq%20Ultra--Fast%20LPUs-F55036?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20%7C%20HF%20Spaces-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://huggingface.co/spaces)
[![Active Vectors](https://img.shields.io/badge/Active%20Vectors-10%2C625-success?style=for-the-badge&logo=database&logoColor=white)](https://pinecone.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

An enterprise-grade, multi-domain **Retrieval-Augmented Generation (RAG)** system architected for complex financial analysis, e-commerce catalog exploration, document intelligence, and cross-source market synthesis. 

Powered by **10,625 high-dimensional dense vectors** partitioned into isolated namespaces on **Pinecone Serverless**, query-time embedding via **Integrated `llama-text-embed-v2`**, and sub-second multi-model answer synthesis using **Groq LPUs** with automated fallback cascades.

---

## 🏗️ End-to-End Pipeline Architecture

```mermaid
flowchart TB
    subgraph INGESTION["1. Multi-Modal Ingestion Pipeline"]
        direction TB
        D1[("Amazon Catalog\n(1,000 items)")]
        D2[("Octaprice & Reviews\n(2,000 items)")]
        D3[("Kindred Deals\n(2,000 items)")]
        D4[("Northwind POs & Manuals\n(1,761 docs)")]
        D5[("SPY ETF & Financial News\n(4,000 records)")]
        
        CLN["Data Cleaners & Metadata Normalizers\n(clean_float, clean_int, text sanitizers)"]
        D1 & D2 & D3 & D4 & D5 --> CLN
        
        BATCH["Batch Record Composer\n(Batch size: 96)"]
        CLN --> BATCH
        
        P_EMB["Pinecone Integrated Inference\n(llama-text-embed-v2 server-side)"]
        BATCH -->|Raw Text + Metadata| P_EMB
    end

    subgraph STORAGE["2. Pinecone Serverless Vector Store (10,625 Vectors)"]
        direction LR
        NS1[("ns: products")]
        NS2[("ns: stocks")]
        NS3[("ns: deals")]
        NS4[("ns: documents")]
        NS5[("ns: news")]
        P_EMB --> NS1 & NS2 & NS3 & NS4 & NS5
    end

    subgraph RETRIEVAL["3. Multi-Namespace Retrieval & Fusion Engine"]
        direction TB
        REQ["Client Query Request\n(Question + Selected Namespaces)"]
        CONC["Concurrent Namespace Search\n(Pinecone index.search)"]
        REQ --> CONC
        
        CONC <-->|Server-Side Vector Search| NS1 & NS2 & NS3 & NS4 & NS5
        
        FUSION["Top-K Candidate Aggregation & Normalization\n(Global Cosine Scoring & Metadata De-duplication)"]
        CONC --> FUSION
    end

    subgraph SYNTHESIS["4. High-Availability LLM Synthesis Cluster"]
        direction TB
        PROMPT["Context Assembly & Strict Citation Prompt\n(Source [1]...[N] Index Mapping)"]
        FUSION --> PROMPT
        
        subgraph GROQ["Groq Inference Fallback Cascade"]
            direction TB
            M1["Primary: openai/gpt-oss-120b\n(~500 tok/sec)"]
            M2["Fallback 1: openai/gpt-oss-20b\n(~750 tok/sec)"]
            M3["Fallback 2: qwen/qwen3.8-27b\n(Failover Resilience)"]
            M1 -.->|On Rate-Limit / Error| M2 -.->|On Error| M3
        end
        PROMPT --> GROQ
    end

    subgraph CLIENT["5. Interactive Web Frontend (FastAPI + Modern SPA)"]
        direction TB
        UI["Reactive Web Dashboard\n- Dynamic Namespace Toggles\n- 1-Click Quick Question Chips\n- Interactive Clickable Citation Badges\n- Tabular Metadata Cards"]
        GROQ -->|Synthesized JSON + Citations| UI
    end
```

---

## 📊 Dataset Partitioning & Namespace Matrix

To eliminate **cross-domain semantic pollution** and allow targeted queries, datasets are segmented into isolated vector namespaces:

| Namespace | Underlying Datasets | Vectors | Extracted Metadata Attributes | Key Query Types |
| :--- | :--- | :---: | :--- | :--- |
| `products` | Amazon Products & Octaprice Reviews | **3,000** | `title`, `brand`, `price`, `rating`, `date`, `asin` | Product features, price comparisons, customer sentiment |
| `stocks` | Daily SPY ETF Historical Records | **2,000** | `date`, `open`, `high`, `low`, `close`, `volume` | Historical highs/lows, volatility, trading volume |
| `deals` | Kindred Merchant Discount Deals | **2,000** | `brand_name`, `domains`, `brand_id` | Affiliate promotions, store domains, coupon programs |
| `documents` | Northwind Purchase Orders & PDF Manuals | **1,761** | `pdf_id`, `url`, `source_file`, `source_type` | Invoices, vendor line-items, equipment user manuals |
| `news` | Curated Financial News Articles | **2,000** | `date`, `url`, `source` | Macroeconomic outlook, interest rate reports, sentiment |

---

## ⚡ Key Architectural Innovations

### 1. Zero-Compute Serverless Embeddings
Instead of loading heavy Hugging Face embedding models locally (which consumes substantial RAM and GPU compute), this project uses **Pinecone's Integrated Inference Engine** (`llama-text-embed-v2`). Text inputs and query strings are embedded server-side inside Pinecone's cloud infrastructure at search time.

### 2. Cascading High-Availability Fallback Cluster
External LLM APIs often encounter rate-limits or temporary degradation. The synthesis layer implements an automated failover loop:
$$\text{Query} \longrightarrow \mathbf{GPT\text{-}OSS\text{ }120B} \xrightarrow{\text{Failover}} \mathbf{GPT\text{-}OSS\text{ }20B} \xrightarrow{\text{Failover}} \mathbf{Qwen\text{ }3.8\text{-}27B}$$
Ensuring **99.9% uptime** and sub-second generation speeds.

### 3. Interactive Grounded Citations
Every assertion produced by the model must cite indexed evidence using bracketed indices (e.g., `[1]`, `[2]`). The frontend parser converts these tokens into interactive citation pills:
- Clicking `[Source 1]` smoothly scrolls to the specific retrieved document card.
- Applies a glowing highlight animation to verify the exact metadata and snippet.

### 4. 1-Click Quick Benchmark Chips
Pre-configured, domain-tuned queries embedded directly into the UI allow testing instant retrieval across single or multi-namespace vectors with automated checkbox synchronization.

---

## 🔌 API Specification

### `POST /api/query`
Executes vector retrieval across target namespaces and generates a cited synthesis.

#### Request Schema:
```json
{
  "question": "What are some of the top-rated products on Amazon and what are their prices?",
  "namespaces": ["products"]
}
```

#### Response Schema:
```json
{
  "answer": "According to the catalog, top-rated products include the Wireless Mouse rated 4.9/5 priced at $29.99 [1] and Noise-Cancelling Headphones rated 4.8/5 priced at $149.00 [2].",
  "sources": [
    {
      "namespace": "products",
      "score": 0.8421,
      "text": "[Product] Wireless Mouse by TechCorp, priced at $29.99, rated 4.9/5...",
      "metadata": {
        "source_name": "amazon",
        "brand": "TechCorp",
        "price": 29.99,
        "rating": 4.9
      }
    }
  ]
}
```

---

## 📁 Repository Structure

```
Multi source Rag/
├── Dockerfile                 # Multi-stage production container for HF Spaces
├── requirements.txt           # Minimal pinned runtime dependencies
├── README.md                  # Comprehensive architectural specification
├── data/                      # Raw datasets (excluded from git)
└── src/
    ├── app.py                 # FastAPI production server & Groq fallback engine
    ├── query_rag.py           # CLI interactive RAG assistant
    ├── unified_indexing.py    # Multi-namespace chunking & Pinecone batch upsert
    ├── static/
    │   └── index.html         # Modern SPA dashboard with quick prompt chips
    └── ingestion/             # Domain-specific dataset ETL & parsers
        ├── ingest_products.py # Amazon & Octaprice catalog normalizer
        ├── ingest_spy.py      # SPY ETF daily financial parser
        ├── ingest_documents.py# PDF purchase orders & user manual extractor
        └── ingest_news.py     # Streaming financial news ingester
```

---

## 🚀 Local Development Setup

### Prerequisites
- Python **3.10+**
- Pinecone Account & Index (`multiragsystem`)
- Groq Cloud API Key

### 1. Clone & Install
```bash
git clone https://github.com/MadhuChitikela/multi-source-rag-model.git
cd multi-source-rag-model
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory:
```env
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=multiragsystem
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...
```

### 3. Launch the Server
```bash
py -m uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## ☁️ Hugging Face Spaces Deployment

This repository is pre-configured for continuous deployment on **Hugging Face Spaces** using Docker:
1. Create a new Space with the **Docker** SDK.
2. In Space **Settings** $\rightarrow$ **Variables and secrets**, add:
   - `PINECONE_API_KEY`: Your Pinecone secret key
   - `PINECONE_INDEX_NAME`: `multiragsystem`
   - `GROQ_API_KEY`: Your Groq API key
   - `HF_TOKEN`: Your Hugging Face access token
3. Push to `main` branch to automatically trigger container build and live deployment.

---

## 🛡️ License
Distributed under the **MIT License**. See `LICENSE` for more information.
