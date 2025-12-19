# src/utils.py
import os

def ensure_directories_exist():
    """Creates necessary folders if they are missing."""
    dirs = ["data/models", "reports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ Checked folder: {d}")