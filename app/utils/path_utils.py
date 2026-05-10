from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*parts)

