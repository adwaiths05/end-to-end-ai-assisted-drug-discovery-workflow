from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path


def parse_smiles_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_csv_text(text: str, smiles_column: str = "smiles") -> list[str]:
    reader = csv.DictReader(StringIO(text))
    return [row[smiles_column].strip() for row in reader if row.get(smiles_column)]


def parse_txt_file(path: Path) -> list[str]:
    return parse_smiles_lines(path.read_text(encoding="utf-8"))

