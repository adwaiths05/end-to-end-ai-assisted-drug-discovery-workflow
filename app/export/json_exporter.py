from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_json(records: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    return path

