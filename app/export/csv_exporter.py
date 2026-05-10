from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_csv(records: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    records.to_csv(path, index=False)
    return path

