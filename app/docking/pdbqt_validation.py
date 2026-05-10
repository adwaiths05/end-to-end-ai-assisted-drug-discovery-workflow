from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

LOGGER = logging.getLogger(__name__)


def validate_receptor_pdbqt(pdbqt_path: Path) -> dict:
    """Validate receptor PDBQT file for docking readiness.
    
    Checks:
    - File exists and has ATOM records
    - Polar hydrogens present (HD atoms)
    - H-bond acceptors present (OA/NA atoms)
    - Protonation ratio reasonable
    
    Returns dict with validation results.
    """
    if not pdbqt_path or not pdbqt_path.exists():
        return {
            "valid": False,
            "error": f"File not found: {pdbqt_path}",
            "atom_count": 0,
            "atom_types": {},
            "hd_count": 0,
            "acceptor_count": 0,
            "protonation_ratio": 0.0,
        }

    atom_types = {}
    charges = []
    n_atoms = 0

    try:
        with open(pdbqt_path) as f:
            for line in f:
                if not line.startswith(("ATOM", "HETATM")):
                    continue
                n_atoms += 1
                # Atom type: last whitespace-delimited token on the line
                parts = line.rstrip().split()
                atype = parts[-1] if parts else "UNK"

                try:
                    charge = float(line[66:76].strip())
                except (ValueError, IndexError):
                    charge = 0.0

                atom_types[atype] = atom_types.get(atype, 0) + 1
                charges.append(charge)
    except Exception as e:
        LOGGER.error(f"Error reading PDBQT file: {e}")
        return {
            "valid": False,
            "error": f"Error reading file: {e}",
            "atom_count": 0,
            "atom_types": {},
            "hd_count": 0,
            "acceptor_count": 0,
            "protonation_ratio": 0.0,
        }

    if n_atoms == 0:
        return {
            "valid": False,
            "error": "No ATOM/HETATM records found",
            "atom_count": 0,
            "atom_types": {},
            "hd_count": 0,
            "acceptor_count": 0,
            "protonation_ratio": 0.0,
        }

    charges_arr = np.array(charges)

    # Check polar hydrogens
    hd_count = atom_types.get("HD", 0)
    has_hd = hd_count > 0

    # Check H-bond acceptors
    oa_count = atom_types.get("OA", 0)
    na_count = atom_types.get("NA", 0)
    has_acceptors = oa_count > 0 or na_count > 0

    # Check protonation ratio
    h_total = sum(v for k, v in atom_types.items() if k.startswith("H"))
    heavy = n_atoms - h_total
    protonation_ratio = h_total / heavy if heavy > 0 else 0

    # Overall validation
    valid = has_hd and has_acceptors

    return {
        "valid": valid,
        "atom_count": n_atoms,
        "atom_types": atom_types,
        "hd_count": hd_count,
        "acceptor_count": oa_count + na_count,
        "protonation_ratio": protonation_ratio,
        "mean_charge": float(charges_arr.mean()),
        "has_polar_hydrogens": has_hd,
        "has_acceptors": has_acceptors,
        "warnings": [
            "No polar hydrogens found — re-generate with polar H support"
            if not has_hd
            else None,
            "No H-bond acceptors found" if not has_acceptors else None,
        ],
    }


def get_ligand_center_from_pdb(pdb_path: Path, hetatm_name: str | None = None) -> tuple[float, float, float] | None:
    """Extract binding box center from co-crystallized ligand in PDB.
    
    Searches for HETATM records with given name (e.g., 'STI' for Imatinib in 1IEP).
    If hetatm_name is None, uses the first non-water HETATM found.
    
    Returns (cx, cy, cz) or None if ligand not found.
    """
    coords = []

    try:
        with open(pdb_path) as f:
            for line in f:
                if not line.startswith("HETATM"):
                    continue

                res_name = line[17:20].strip()

                # Skip water
                if res_name == "HOH":
                    continue

                # If specific name given, filter by it
                if hetatm_name and res_name != hetatm_name:
                    continue

                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append((x, y, z))
                except (ValueError, IndexError):
                    continue

        if not coords:
            LOGGER.warning(f"No ligand atoms found in {pdb_path}")
            return None

        # Compute center of mass
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        zs = [c[2] for c in coords]

        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        cz = sum(zs) / len(zs)

        LOGGER.info(f"Ligand center from {len(coords)} atoms: [{cx:.3f}, {cy:.3f}, {cz:.3f}]")
        return (cx, cy, cz)

    except Exception as e:
        LOGGER.error(f"Error extracting ligand center: {e}")
        return None
