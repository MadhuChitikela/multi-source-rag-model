import os
import pandas as pd
from pathlib import Path
from datasets import load_dataset

def ingest_northwind_purchase_orders(hf_token=None):
    """
    Ingest AyoubChLin/northwind_PurchaseOrders from Hugging Face.
    Contains purchase orders and invoices.
    """
    dataset_name = "AyoubChLin/northwind_PurchaseOrders"
    print(f"[INFO] Ingesting HF dataset: {dataset_name}")
    try:
        if hf_token:
            dataset = load_dataset(dataset_name, token=hf_token)
        else:
            dataset = load_dataset(dataset_name)
            
        print(f"[INFO] Successfully loaded {dataset_name} from Hugging Face.")
        print(f"[INFO] Splits: {list(dataset.keys())}")
        
        # Usually it has a 'train' split
        primary_split = list(dataset.keys())[0]
        df = pd.DataFrame(dataset[primary_split])
        print(f"[INFO] Northwind Purchase Orders shape: {df.shape}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to ingest {dataset_name}: {e}")
        return None

def ingest_user_manual_links(data_dir: Path):
    """
    Ingest user manual links from denis-postanogov/UserManualPdf100.
    Finds markdown or text files containing manual descriptions and links.
    """
    manuals_dir = data_dir / "user_manual_pdf100"
    if not manuals_dir.exists():
        print(f"[ERROR] User manuals directory not found at {manuals_dir}")
        return None
        
    print(f"[INFO] Parsing user manual links from {manuals_dir}")
    # Search for markdown, text, or csv files containing links
    files = list(manuals_dir.glob("**/*"))
    text_files = [f for f in files if f.suffix in ('.md', '.txt', '.csv')]
    
    extracted_manuals = []
    for file in text_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parse markdown links or csv lines containing PDFs
                # Simple extraction: find lines containing '.pdf' or web links
                for line in content.split('\n'):
                    if 'http' in line and '.pdf' in line:
                        extracted_manuals.append({
                            'source_file': file.name,
                            'entry': line.strip()
                        })
        except Exception as e:
            print(f"[WARNING] Could not read file {file.name}: {e}")
            
    df_manuals = pd.DataFrame(extracted_manuals)
    print(f"[INFO] Found {len(df_manuals)} user manual links.")
    return df_manuals

if __name__ == "__main__":
    # Test execution
    project_root = Path(__file__).resolve().parents[2]
    data_directory = project_root / "data"
    
    # Use environment token if available
    hf_token = os.environ.get("HF_TOKEN")
    
    df_orders = ingest_northwind_purchase_orders(hf_token)
    df_manuals = ingest_user_manual_links(data_directory)
