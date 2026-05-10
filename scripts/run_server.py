from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

