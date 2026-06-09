# Multi-Source Finance & E-Commerce RAG System

A production-grade, multi-source Retrieval-Augmented Generation (RAG) system. This application ingests, structures, chunks, and indexes data across **five distinct domains** into a unified Pinecone serverless index, then serves it via a FastAPI backend and a lightweight, responsive light-mode frontend web app.

---

## 🚀 Key Features

* **Multi-Source Ingestion**: Ingests, cleans, and indexes seven raw datasets:
  * Amazon Products (e-commerce listings)
  * Octaprice Products & Reviews (CSV and JSON archives)
  * Kindred Deals (merchant discounts and domains)
  * Northwind Purchase Orders (extracted PDF text)
  * User Manuals (web reference documentation links)
  * Daily SPY ETF Stock Prices (historical market metrics)
  * Financial News (gated Hugging Face dataset)
* **Serverless Integrated Embeddings**: Utilizes Pinecone's server-side embedding inference model (`llama-text-embed-v2`) via `upsert_records()` and `search()`, eliminating local vector generation overhead.
* **Namespace Segmentation**: Separates data into 5 target namespaces (`products`, `stocks`, `deals`, `documents`, `news`) to allow precise filtering.
* **FastAPI Backend**: Exposes a structured `/api/query` POST endpoint, queries selected namespaces, ranks results, and synthesizes answers using **Groq LLM** with bracketed citations.
* **Lightweight Light-Mode Frontend**: 
  - Minimalistic, high-speed single-page application with customized checkbox filters for target namespaces.
  - Interactive citation badges: clicking on references in the answer (e.g., `[Source 1]`) smoothly scrolls to and highlights the corresponding source document in the sidebar.
  - Tabular property grids that clean and layout document metadata fields (scores, prices, dates, ratings, URLs).

---

## 📁 Project Structure

```
Multi source Rag/
├── data/                      # Raw datasets (excluded from Git)
├── src/
│   ├── ingestion/             # Cleaners and loading scripts for datasets
│   │   ├── ingest_products.py
│   │   ├── ingest_spy.py
│   │   ├── ingest_documents.py
│   │   └── ingest_news.py
│   ├── static/
│   │   └── index.html         # Lightweight frontend UI
│   ├── app.py                 # FastAPI backend server
│   ├── query_rag.py           # CLI version of the RAG assistant
│   └── unified_indexing.py    # Pipeline to chunk and index samples into Pinecone
├── .gitignore                 # Prevents pushing data and API keys
├── .env                       # Local secrets (excluded from Git)
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## 🔧 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MadhuChitikela/multi-source-rag-model.git
   cd multi-source-rag-model
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root with the following parameters:
   ```env
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=multiragsystem
   GROQ_API_KEY=your_groq_api_key
   HF_TOKEN=your_huggingface_token_for_gated_news
   ```

---

## 🏃 Run the Application

Start the FastAPI backend server using Uvicorn:
```bash
py -m uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to query the indexed knowledge base interactively.

---

## 🧪 Example Test Queries

* **Stocks (`stocks` selected)**: *"What was the SPY closing price on 2025-08-26?"*
* **Deals (`deals` selected)**: *"Show me deals from Kindred. What domains are associated with them?"*
* **Documents (`documents` selected)**: *"What details or companies are mentioned in the Northwind purchase orders?"*
* **Multi-Source (`stocks` + `news` selected)**: *"Compare the SPY stock price on August 25, 2025 with the financial news indicators reported at that time."*
