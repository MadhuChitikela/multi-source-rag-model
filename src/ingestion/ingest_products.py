import os
import json
import zipfile
import pandas as pd
from pathlib import Path

def ingest_amazon_products(data_dir: Path):
    """Ingest Amazon product samples dataset."""
    amazon_dir = data_dir / "amazon_products_sample"
    if not amazon_dir.exists():
        print(f"[ERROR] Amazon products directory not found at {amazon_dir}")
        return None
        
    # Search for Parquet, CSV, or JSON files
    files = list(amazon_dir.glob("**/*"))
    data_files = [f for f in files if f.suffix in ('.parquet', '.csv', '.json')]
    
    if not data_files:
        print(f"[WARNING] No data files found in {amazon_dir}")
        return None
        
    dfs = []
    for file in data_files:
        print(f"[INFO] Loading Amazon product data from {file.name}")
        try:
            if file.suffix == '.parquet':
                dfs.append(pd.read_parquet(file))
            elif file.suffix == '.csv':
                dfs.append(pd.read_csv(file))
            elif file.suffix == '.json':
                dfs.append(pd.read_json(file))
        except Exception as e:
            print(f"[ERROR] Failed to load {file.name}: {e}")
            
    if not dfs:
        return None
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"[INFO] Combined Amazon products shape: {df.shape}")
    return df

def ingest_ecommerce_products(data_dir: Path):
    """
    Extract CSVs from ZIP archives and load them as DataFrames.
    Also parse any JSON review files.
    """
    ecom_dir = data_dir / "ecommerce_product_dataset"
    if not ecom_dir.exists():
        print(f"[ERROR] E-commerce products directory not found at {ecom_dir}")
        return None
        
    all_dfs = []
    
    # Extract ZIP files containing CSVs
    zip_files = list(ecom_dir.glob("**/*.zip"))
    for zip_path in zip_files:
        print(f"[INFO] Extracting e-commerce dataset from ZIP: {zip_path.name}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                for csv_name in csv_files:
                    with zf.open(csv_name) as f:
                        df = pd.read_csv(f)
                        df['source_zip'] = zip_path.name
                        all_dfs.append(df)
        except Exception as e:
            print(f"[ERROR] Failed to read ZIP {zip_path.name}: {e}")
            
    # Read JSON review files
    json_files = list(ecom_dir.glob("**/*.json"))
    for json_path in json_files:
        if json_path.name.endswith('.schema.json') or json_path.name == 'metadata.json':
            continue
        print(f"[INFO] Reading e-commerce reviews from JSON: {json_path.name}")
        try:
            # Mercadolivre files are standard JSON arrays
            try:
                df = pd.read_json(json_path)
            except Exception:
                df = pd.read_json(json_path, lines=True)
            df['source_json'] = json_path.name
            all_dfs.append(df)
        except Exception as e:
            print(f"[ERROR] Failed to read JSON {json_path.name}: {e}")
            
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        print(f"[INFO] Loaded {len(combined)} rows from Octaprice archives")
        return combined
    else:
        print("[WARNING] No CSV/JSON files found in Octaprice archives")
        return None

def ingest_kindred_deals(data_dir: Path):
    """Ingest Kindred ecommerce deals dataset."""
    deals_dir = data_dir / "kindred_deals_dataset"
    if not deals_dir.exists():
        print(f"[ERROR] Kindred deals directory not found at {deals_dir}")
        return None
        
    files = list(deals_dir.glob("**/*"))
    data_files = [f for f in files if f.suffix in ('.csv', '.jsonl', '.json')]
    
    if not data_files:
        print(f"[WARNING] No deals files found in {deals_dir}")
        return None
        
    dfs = []
    # Limit number of records read if files are extremely large (e.g. 4M discount codes)
    for file in data_files:
        print(f"[INFO] Loading kindred deals dataset from {file.name}")
        try:
            if file.suffix == '.csv':
                # Read first 10,000 rows as sample or read fully if memory permits
                dfs.append(pd.read_csv(file, nrows=10000))
            elif file.suffix == '.jsonl':
                lines = []
                with open(file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 10000:  # Sample limit
                            break
                        lines.append(json.loads(line))
                dfs.append(pd.DataFrame(lines))
        except Exception as e:
            print(f"[ERROR] Failed to load {file.name}: {e}")
            
    if not dfs:
        return None
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"[INFO] Combined Kindred deals shape (sampled): {df.shape}")
    return df

if __name__ == "__main__":
    # Test execution
    project_root = Path(__file__).resolve().parents[2]
    data_directory = project_root / "data"
    
    df_amazon = ingest_amazon_products(data_directory)
    df_ecom = ingest_ecommerce_products(data_directory)
    df_deals = ingest_kindred_deals(data_directory)
