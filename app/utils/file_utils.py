from __future__ import annotations

from pathlib import Path


def safe_filename(name: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-", "."} else "_" for char in name)


def unique_output_path(directory: Path, stem: str, suffix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{safe_filename(stem)}{suffix}"

