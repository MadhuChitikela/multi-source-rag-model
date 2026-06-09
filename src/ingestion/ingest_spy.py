import os
import pandas as pd
from pathlib import Path

def ingest_spy_data(data_dir: Path):
    """
    Ingest Daily SPY ETF data.
    Expected file: data_dir / "daily_spy_data" / "*.csv"
    """
    spy_dir = data_dir / "daily_spy_data"
    if not spy_dir.exists():
        print(f"[ERROR] SPY directory not found at {spy_dir}")
        return None
    
    csv_files = list(spy_dir.glob("*.csv"))
    if not csv_files:
        # Check subdirectories just in case
        csv_files = list(spy_dir.rglob("*.csv"))
        
    if not csv_files:
        print(f"[ERROR] No CSV file found in {spy_dir}")
        return None
        
    csv_file = csv_files[0]
    print(f"[INFO] Ingesting SPY data from {csv_file}")
    
    # Skip the ticker row and empty row, keeping the header row, then load
    df = pd.read_csv(csv_file, skiprows=[1, 2])
    
    # Rename the first column (originally 'Price' but contains dates)
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ensure numeric columns are float
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    print(f"[INFO] Loaded {len(df)} rows of SPY data spanning from {df['Date'].min()} to {df['Date'].max()}")
    return df

if __name__ == "__main__":
    # Test execution
    project_root = Path(__file__).resolve().parents[2]
    data_directory = project_root / "data"
    df_spy = ingest_spy_data(data_directory)
    if df_spy is not None:
        print(df_spy.head())
