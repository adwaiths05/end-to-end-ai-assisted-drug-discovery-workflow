from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)
VINA_EXECUTABLE = Path(r"D:\tools\vina\vina.exe")


class VinaRunner:
    def __init__(self, receptor_pdbqt: Path, center: tuple[float, float, float], box_size: tuple[float, float, float], exhaustiveness: int = 8, n_poses: int = 5) -> None:
        self.receptor_pdbqt = receptor_pdbqt
        self.center = center
        self.box_size = box_size
        self.exhaustiveness = exhaustiveness
        self.n_poses = n_poses

    def dock(self, ligand_pdbqt: Path):
        """Run Vina docking via subprocess."""
        work_dir = ligand_pdbqt.parent
        output_pdbqt = work_dir / f"{ligand_pdbqt.stem}_out.pdbqt"
        log_file = work_dir / f"{ligand_pdbqt.stem}_log.txt"

        # Build Vina command
        # Use explicit center_x/center_y/center_z and size_x/size_y/size_z flags
        cmd = [
            str(VINA_EXECUTABLE),
            "--receptor",
            str(self.receptor_pdbqt),
            "--ligand",
            str(ligand_pdbqt),
            "--center_x",
            str(self.center[0]),
            "--center_y",
            str(self.center[1]),
            "--center_z",
            str(self.center[2]),
            "--size_x",
            str(self.box_size[0]),
            "--size_y",
            str(self.box_size[1]),
            "--size_z",
            str(self.box_size[2]),
            "--exhaustiveness",
            str(self.exhaustiveness),
            "--num_modes",
            str(self.n_poses),
            "--out",
            str(output_pdbqt),
        ]

        try:
            # Run Vina
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Write stdout to log file manually since --log isn't supported in all Vina versions
            log_file.write_text(result.stdout, encoding="utf-8")
            
            if result.returncode != 0:
                LOGGER.error(f"Vina failed: {result.stderr or result.stdout}")
                raise RuntimeError(f"Vina exited with code {result.returncode}: {result.stderr or result.stdout}")

            # Parse log file for binding affinity values
            energies = self._parse_vina_log(log_file)
            best_energy = float(energies[0]) if energies else None

            return {
                "best_energy": best_energy,
                "energies": energies,
                "pose_file": str(output_pdbqt)
            }
        except subprocess.TimeoutExpired:
            LOGGER.error("Vina docking timed out after 300 seconds")
            raise RuntimeError("Vina docking timed out")
        except Exception as exc:
            LOGGER.error(f"Vina docking error: {exc}")
            raise

    def _parse_vina_log(self, log_file: Path) -> list[float]:
        """Extract binding affinity values from Vina log file."""
        if not log_file.exists():
            LOGGER.warning(f"Vina log file not found: {log_file}")
            return []

        energies = []
        try:
            with open(log_file, "r") as f:
                for line in f:
                    # More lenient regex to capture affinities like -7, -7.0, -7.22 etc.
                    match = re.search(r"^\s+\d+\s+([-+]?\d*\.?\d+)", line)
                    if match:
                        energies.append(float(match.group(1)))
        except Exception as exc:
            LOGGER.warning(f"Failed to parse Vina log: {exc}")

        return energies

