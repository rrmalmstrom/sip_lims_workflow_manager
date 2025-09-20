
import sys
from pathlib import Path
Path("project.db").write_text("modified content")
print("Failing script", file=sys.stderr)
sys.exit(1)
