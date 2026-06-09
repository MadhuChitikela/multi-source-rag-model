import os
import pandas as pd
from pathlib import Path
from datasets import load_dataset

def ingest_financial_news(hf_token=None, stream=True, max_rows=1000):
    """
    Ingest Brianferrell787/financial-news-multisource from Hugging Face.
    Provides option to stream or load fully. Default stream=True, max_rows=1000.
    """
    dataset_name = "Brianferrell787/financial-news-multisource"
    print(f"[INFO] Ingesting financial news dataset: {dataset_name} (stream={stream})")
    
    try:
        kwargs = {"token": hf_token} if hf_token else {}
        
        if stream:
            # Using streaming=True loads data on-the-fly without downloading the whole 57M rows
            dataset = load_dataset(dataset_name, streaming=True, **kwargs)
            primary_split = list(dataset.keys())[0] if list(dataset.keys()) else 'train'
            stream_dataset = dataset[primary_split]
            
            # Fetch a sample of rows
            sampled_rows = []
            for i, row in enumerate(stream_dataset):
                if i >= max_rows:
                    break
                sampled_rows.append(row)
                
            df = pd.DataFrame(sampled_rows)
            print(f"[INFO] Streamed and loaded {len(df)} sample rows from financial news.")
            return df
        else:
            dataset = load_dataset(dataset_name, **kwargs)
            primary_split = list(dataset.keys())[0]
            df = pd.DataFrame(dataset[primary_split])
            print(f"[INFO] Fully loaded financial news dataset shape: {df.shape}")
            return df
            
    except Exception as e:
        print(f"[ERROR] Failed to ingest financial news: {e}")
        return None

if __name__ == "__main__":
    # Test execution
    # Use environment token if available
    hf_token = os.environ.get("HF_TOKEN")
    df_news = ingest_financial_news(hf_token=hf_token, stream=True, max_rows=10)
    if df_news is not None:
        print(df_news.head())
