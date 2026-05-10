from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    project_root: Path = Path(__file__).resolve().parents[1]
    artifact_dir: Path = project_root / "artifacts"
    data_dir: Path = project_root / "data"
    output_dir: Path = data_dir / "output"
    screening_dir: Path = data_dir / "screening"
    docking_dir: Path = data_dir / "docking"
    receptor_id: str = "1IEP"
    receptor_pdb_url: str = "https://files.rcsb.org/download/1IEP.pdb"
    docking_box_center: tuple[float, float, float] = (15.0, 53.0, 18.0)
    docking_box_size: tuple[float, float, float] = (25.0, 25.0, 25.0)
    docking_exhaustiveness: int = 8
    docking_n_poses: int = 5
    random_seed: int = 42
    top_hits: int = 50
    top_consensus_hits: int = 10
    confidence_quantile: float = 0.75
    required_models: tuple[str, ...] = ("rf", "mpnn", "gin")


settings = AppConfig()
