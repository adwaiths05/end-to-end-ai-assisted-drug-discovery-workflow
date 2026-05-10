from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class DockingConfig:
    receptor_id: str = settings.receptor_id
    receptor_pdb_url: str = settings.receptor_pdb_url
    box_center: tuple[float, float, float] = settings.docking_box_center
    box_size: tuple[float, float, float] = settings.docking_box_size
    exhaustiveness: int = settings.docking_exhaustiveness
    n_poses: int = settings.docking_n_poses

