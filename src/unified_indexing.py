import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone
from tqdm import tqdm
import time
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.ingest_products import (
    ingest_amazon_products,
    ingest_ecommerce_products,
    ingest_kindred_deals
)
from src.ingestion.ingest_documents import (
    ingest_northwind_purchase_orders,
    ingest_user_manual_links
)
from src.ingestion.ingest_spy import ingest_spy_data
from src.ingestion.ingest_news import ingest_financial_news

load_dotenv()

# ------------------------- Configuration -------------------------
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "multiragsystem")   # Pinecone index name
BATCH_SIZE = 96                   # Batch size for upsert_records (96 is recommended)
DATA_DIR = Path("data")

# Initialize Pinecone if API key is provided
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
else:
    print("[WARNING] PINECONE_API_KEY not found in environment. Pinecone operations will be mocked.")
    index = None

# Helper to safely clean and convert prices/ratings to floats
def clean_float(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace('"', '').replace("'", '').replace('$', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return None

# Helper to safely clean and convert values to integers
def clean_int(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace('"', '').replace("'", '').replace(',', '').strip()
    try:
        return int(float(val_str))
    except ValueError:
        return None

# ------------------------- Data Loaders -------------------------
def load_amazon():
    return ingest_amazon_products(DATA_DIR)

def load_octaprice():
    return ingest_ecommerce_products(DATA_DIR)

def load_kindred():
    return ingest_kindred_deals(DATA_DIR)

def load_northwind():
    return ingest_northwind_purchase_orders()

def load_manual_links():
    return ingest_user_manual_links(DATA_DIR)

def load_spy():
    return ingest_spy_data(DATA_DIR)

def load_news(sample_size=1000):
    hf_token = os.environ.get("HF_TOKEN")
    return ingest_financial_news(hf_token=hf_token, stream=True, max_rows=sample_size)

# ------------------------- Formatting Functions -------------------------
def format_amazon(row):
    title = str(row.get('title', '')).strip()
    brand = str(row.get('brand', '')).strip()
    price = row.get('final_price')
    rating = row.get('rating')
    desc = str(row.get('description', '')).strip()[:500]
    
    chunk = f"[Product] {title}"
    if brand and brand != 'nan':
        chunk += f" by {brand}"
    cleaned_price = clean_float(price)
    if cleaned_price:
        chunk += f", priced at ${cleaned_price:.2f}"
    cleaned_rating = clean_float(rating)
    if cleaned_rating:
        chunk += f", rated {cleaned_rating}/5"
    if desc and desc != 'nan':
        chunk += f". {desc}"
        
    metadata = {
        "source_type": "product",
        "source_name": "amazon",
        "product_id": str(row.get('asin', '')),
        "title": title,
        "brand": brand if brand != 'nan' else "",
        "price": cleaned_price,
        "rating": cleaned_rating,
    }
    return chunk, metadata

def format_octaprice(row):
    # Differentiate between reviews (JSON) and product listings (CSV)
    source_json = row.get('source_json')
    if pd.notna(source_json):
        # Review row
        content = str(row.get('content', '')).strip()
        rating = row.get('rating')
        date = str(row.get('date', '')).strip()
        
        chunk = f"[Review] Customer review ({rating}/5) on {date}: {content}"
        metadata = {
            "source_type": "review",
            "source_name": "octaprice_reviews",
            "rating": clean_float(rating),
            "date": date,
        }
    else:
        # Product listing row
        title = str(row.get('name', row.get('title', ''))).strip()
        brand = str(row.get('brandName', '')).strip()
        price = row.get('price')
        desc = str(row.get('description', '')).strip()[:500]
        
        chunk = f"[Product] {title}"
        if brand and brand != 'nan':
            chunk += f" by {brand}"
        cleaned_price = clean_float(price)
        if cleaned_price:
            chunk += f", priced at ${cleaned_price:.2f}"
        if desc and desc != 'nan':
            chunk += f". {desc}"
            
        metadata = {
            "source_type": "product",
            "source_name": "octaprice_products",
            "title": title,
            "brand": brand if brand != 'nan' else "",
            "price": cleaned_price,
        }
    return chunk, metadata

def format_kindred(row):
    name = str(row.get('name', '')).strip()
    domains = str(row.get('domains', '')).strip()
    
    chunk = f"[Deal] Brand: {name}"
    if domains and domains != 'nan':
        chunk += f" (domains: {domains})"
        
    metadata = {
        "source_type": "deal",
        "source_name": "kindred",
        "brand_id": str(row.get('brand_id', '')),
        "brand_name": name,
        "domains": domains if domains != 'nan' else "",
    }
    return chunk, metadata

def format_northwind(row):
    pdf = row.get('pdf')
    text_parts = []
    if pdf:
        try:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            
    full_text = "\n".join(text_parts).strip()
    if not full_text:
        full_text = "Purchase order PDF from Northwind dataset."
        
    chunk = f"[Document] {full_text}"
    metadata = {
        "source_type": "document",
        "source_name": "northwind",
        "pdf_id": str(row.name),
    }
    return chunk, metadata

def format_manual(row):
    entry = str(row.get('entry', '')).strip()
    source_file = str(row.get('source_file', '')).strip()
    
    url = ""
    for part in entry.split():
        if part.startswith('http'):
            url = part
            break
    if not url:
        url = entry
        
    chunk = f"[Manual] User manual PDF: {entry}"
    metadata = {
        "source_type": "manual_link",
        "source_name": "user_manual",
        "url": url,
        "source_file": source_file,
    }
    return chunk, metadata

def format_spy(row):
    date = row['Date']
    date_str = str(date)[:10] if pd.notna(date) else ""
    
    chunk = f"[Stock] SPY on {date_str}: Open ${row['Open']:.2f}, High ${row['High']:.2f}, Low ${row['Low']:.2f}, Close ${row['Close']:.2f}, Volume {int(row['Volume'])}"
    metadata = {
        "source_type": "stock",
        "source_name": "spy",
        "date": date_str,
        "open": clean_float(row['Open']),
        "high": clean_float(row['High']),
        "low": clean_float(row['Low']),
        "close": clean_float(row['Close']),
        "volume": clean_int(row['Volume']),
    }
    return chunk, metadata

def format_news(row):
    text = str(row.get('text', '')).strip()[:2000]
    chunk = f"[News] {text}"
    
    # Safely parse JSON string for extra_fields
    extra_str = row.get('extra_fields', '{}')
    extra = {}
    if isinstance(extra_str, str):
        try:
            extra = json.loads(extra_str)
        except Exception:
            pass
    elif isinstance(extra_str, dict):
        extra = extra_str
        
    metadata = {
        "source_type": "news",
        "source_name": "financial_news",
        "date": str(row.get('date', '')),
        "url": str(extra.get('url', '')),
        "source": str(extra.get('source', '')),
    }
    return chunk, metadata

# ------------------------- Indexing Orchestrator -------------------------
def index_dataset(data, formatter, namespace, name):
    if data is None or len(data) == 0:
        print(f"Skipping {name}: no data found")
        return
        
    records = []
    for idx, row in data.iterrows():
        try:
            chunk, meta = formatter(row)
            if not chunk or len(chunk) < 10:
                continue
            dataset_key = name.lower().replace(" ", "_")
            records.append({
                "id": f"{namespace}_{dataset_key}_{idx}",
                "text": chunk,
                "metadata": meta
            })
        except Exception as e:
            print(f"Error formatting row {idx} for {name}: {e}")
            
    total = len(records)
    print(f"\nIndexing {total} records for {name} into namespace '{namespace}'")
    
    if index is None:
        print(f"[MOCK] Would upsert {total} records to namespace '{namespace}' (Mock mode active - no API key)")
        return
        
    for i in tqdm(range(0, total, BATCH_SIZE), desc=f"Uploading {name}", ascii=True):
        batch = records[i:i+BATCH_SIZE]
        records_batch = []
        for rec in batch:
            # Flatten metadata fields alongside _id and text for upsert_records
            rec_dict = {
                "_id": rec["id"],
                "text": rec["text"]
            }
            if rec["metadata"]:
                for k, v in rec["metadata"].items():
                    if v is not None:
                        rec_dict[k] = v
            records_batch.append(rec_dict)
        try:
            index.upsert_records(namespace=namespace, records=records_batch)
        except Exception as e:
            print(f"\n[ERROR] Pinecone upsert failed for batch {i//BATCH_SIZE}: {e}")
        time.sleep(0.1)  # avoid rate limiting
    print(f"Completed indexing for: {name}")

# ------------------------- Main Ingestion Pipeline -------------------------
def main():
    print("============================================================")
    print("STARTING UNIFIED DATA INGESTION AND INDEXING PIPELINE")
    print("============================================================\n")
    
    print("1. Loading datasets...")
    
    try:
        amazon_df = load_amazon()
    except Exception as e:
        print(f"Error loading Amazon: {e}")
        amazon_df = None
        
    try:
        octaprice_df = load_octaprice()
    except Exception as e:
        print(f"Error loading Octaprice: {e}")
        octaprice_df = None
        
    try:
        kindred_df = load_kindred()
    except Exception as e:
        print(f"Error loading Kindred: {e}")
        kindred_df = None
        
    try:
        northwind_df = load_northwind()
    except Exception as e:
        print(f"Error loading Northwind: {e}")
        northwind_df = None
        
    try:
        manuals_df = load_manual_links()
    except Exception as e:
        print(f"Error loading Manuals: {e}")
        manuals_df = None
        
    try:
        spy_df = load_spy()
    except Exception as e:
        print(f"Error loading SPY: {e}")
        spy_df = None
        
    try:
        news_df = load_news(sample_size=1000)
    except Exception as e:
        print(f"Error loading News: {e}")
        news_df = None

    print("\n2. Processing and Indexing into Pinecone...")
    
    # Slice datasets to MAX_RECORDS to keep indexing times reasonable and free-tier safe
    MAX_RECORDS = 1000
    
    index_dataset(amazon_df.head(MAX_RECORDS) if amazon_df is not None else None, format_amazon, "products", "Amazon Products")
    index_dataset(octaprice_df.head(MAX_RECORDS) if octaprice_df is not None else None, format_octaprice, "products", "Octaprice Products")
    index_dataset(kindred_df.head(MAX_RECORDS) if kindred_df is not None else None, format_kindred, "deals", "Kindred Deals")
    index_dataset(northwind_df.head(MAX_RECORDS) if northwind_df is not None else None, format_northwind, "documents", "Northwind Purchase Orders")
    index_dataset(manuals_df.head(MAX_RECORDS) if manuals_df is not None else None, format_manual, "documents", "User Manual Links")
    index_dataset(spy_df.tail(MAX_RECORDS) if spy_df is not None else None, format_spy, "stocks", "SPY ETF Data")
    index_dataset(news_df.head(MAX_RECORDS) if news_df is not None else None, format_news, "news", "Financial News")

    if index is not None:
        try:
            stats = index.describe_index_stats()
            print("\nFinal Pinecone Index Stats:")
            print(f"   Total vectors: {stats['total_vector_count']}")
            for ns, info in stats['namespaces'].items():
                print(f"   Namespace '{ns}': {info['vector_count']} vectors")
        except Exception as e:
            print(f"Could not retrieve Pinecone index statistics: {e}")
    else:
        print("\nPipeline run completed in MOCK mode.")

if __name__ == "__main__":
    main()
