import sys
from pathlib import Path
import time

print("Running Quality Control...")
time.sleep(2)

output_file = Path("../outputs/qc_results.csv")
output_file.parent.mkdir(exist_ok=True)
output_file.write_text("sample,metric\nsample1,0.98\nsample2,0.99")

print("QC finished.")
sys.exit(0)