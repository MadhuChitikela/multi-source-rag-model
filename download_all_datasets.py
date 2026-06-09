import subprocess
import shutil
import os
from pathlib import Path
import sys

def run_cmd(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   [WARNING] Command failed: {result.stderr}")
        return False
    return True

def clone_repo(repo_url, dest_dir):
    """Clone a GitHub repository shallowly (depth 1) into a specific folder."""
    print(f"   Cloning {repo_url} -> {dest_dir}")
    # Remove existing directory to avoid conflicts
    if os.path.exists(dest_dir):
        try:
            shutil.rmtree(dest_dir)
        except Exception as e:
            print(f"   Failed to remove existing directory {dest_dir}: {e}")
            # Try running rm -rf command or ignore if directory empty
    cmd = f'git clone --depth 1 "{repo_url}" "{dest_dir}"'
    return run_cmd(cmd)

def download_hf_dataset(dataset_name, hf_token=None):
    """Download a Hugging Face dataset using the datasets library."""
    print(f"   Downloading HF dataset: {dataset_name}")
    try:
        from datasets import load_dataset
    except ImportError:
        print("   Please install the 'datasets' library first: pip install datasets")
        return False

    try:
        # Pass token if provided.
        if hf_token:
            dataset = load_dataset(dataset_name, token=hf_token, trust_remote_code=True)
        else:
            dataset = load_dataset(dataset_name, trust_remote_code=True)
        print(f"   [SUCCESS] Downloaded {dataset_name}")
        return True
    except Exception as e:
        print(f"   [ERROR] Failed to download {dataset_name}: {e}")
        return False

def main():
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Store absolute path to data dir
    data_dir_abs = data_dir.resolve()

    # GitHub Repositories to clone (expected targets)
    repos = [
        ("https://github.com/bright-cn/Amazon-dataset-samples.git", "amazon_products_sample"),
        ("https://github.com/octaprice/ecommerce-product-dataset.git", "ecommerce_product_dataset"),
        ("https://github.com/kindred-app/kindred-ecommerce-merchant-deals-dataset.git", "kindred_deals_dataset"),
        ("https://github.com/denis-postanogov/UserManualPdf100.git", "user_manual_pdf100"),
        ("https://github.com/OStochastic/Daily-SPY-data-from-2000-2025.git", "daily_spy_data")
    ]

    for url, dest in repos:
        dest_path = data_dir_abs / dest
        print(f"Cloning {url} to {dest_path}...")
        clone_repo(url, str(dest_path))
        # Clean up .git folders to save space (optional)
        git_dir = dest_path / ".git"
        if git_dir.exists():
            try:
                shutil.rmtree(git_dir)
            except Exception as e:
                print(f"   Failed to clean up .git for {dest}: {e}")

    # Hugging Face datasets
    hf_datasets = [
        "AyoubChLin/northwind_PurchaseOrders",
        "Brianferrell787/financial-news-multisource"
    ]

    # Use the token provided by the user, fallback to env variable if set
    hf_token = os.environ.get("HF_TOKEN")

    for ds in hf_datasets:
        download_hf_dataset(ds, hf_token)

if __name__ == "__main__":
    main()
