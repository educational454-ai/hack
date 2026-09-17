"""Server startup script for Evidence-First Misinformation Analyzer."""

import sys
from pathlib import Path
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    print("Starting AI-03 Evidence-First Misinformation Analyzer server on http://127.0.0.1:8000 ...")
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
