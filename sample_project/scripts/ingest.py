import sys
from pathlib import Path
import time

print("Starting data ingestion...")
time.sleep(2) # Simulate work

log_file = Path("../outputs/ingestion.log")
log_file.parent.mkdir(exist_ok=True)
log_file.write_text("Data ingestion completed successfully.")

print("Data ingestion finished.")
sys.exit(0)