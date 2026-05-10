from __future__ import annotations

import logging
import math
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)

# AutoDock atom type mapping
AD_ATOM_MAP = {
    "C": "C",
    "N": "NA",
    "O": "OA",
    "S": "SA",
    "H": "HD",
    "P": "P",
    "F": "F",
    "CL": "CL",
    "BR": "BR",
    "I": "I",
}

PROLINE = "PRO"


def download_receptor_pdb(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def strip_receptor_pdb(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("ATOM") or line.startswith("TER") or line.startswith("END"):
            lines.append(line)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _parse_pdb_atoms(pdb_path: Path) -> list[dict]:
    """Parse ATOM records from PDB file."""
    atoms = []
    for line in pdb_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            atom = {
                "record": line[0:6].strip(),
                "serial": int(line[6:11]),
                "name": line[12:16].strip(),
                "res_name": line[17:20].strip(),
                "chain": line[21],
                "res_seq": int(line[22:26]),
                "x": float(line[30:38]),
                "y": float(line[38:46]),
                "z": float(line[46:54]),
                "element": line[76:78].strip() if len(line) > 77 else line[12:16].strip()[0],
            }
            atoms.append(atom)
        except (ValueError, IndexError):
            continue
    return atoms


def _normalize_vector(v: list[float]) -> list[float]:
    """Normalize a 3D vector."""
    magnitude = math.sqrt(sum(c * c for c in v))
    return [c / magnitude for c in v] if magnitude > 0 else v


def _add_backbone_nh(atoms: list[dict]) -> list[dict]:
    """Add polar hydrogens to backbone N atoms (except proline)."""
    # Index atoms by (chain, res_seq, atom_name)
    res_dict = {}
    for atom in atoms:
        key = (atom["chain"], atom["res_seq"])
        if key not in res_dict:
            res_dict[key] = {}
        res_dict[key][atom["name"]] = atom

    new_h = []
    for (chain, res_seq), res in sorted(res_dict.items()):
        if "N" not in res:
            continue
        n_atom = res["N"]
        if n_atom["res_name"] == PROLINE:
            continue  # Proline N has no H
        if "CA" not in res:
            continue

        ca = res["CA"]
        prev_key = (chain, res_seq - 1)

        if prev_key in res_dict and "C" in res_dict[prev_key]:
            # Standard residue: H points along bisector of (C_prev->N) and (N->CA)
            c_prev = res_dict[prev_key]["C"]
            v1 = _normalize_vector(
                [n_atom["x"] - c_prev["x"], n_atom["y"] - c_prev["y"], n_atom["z"] - c_prev["z"]]
            )
            v2 = _normalize_vector([ca["x"] - n_atom["x"], ca["y"] - n_atom["y"], ca["z"] - n_atom["z"]])
            direction = _normalize_vector([v1[i] - v2[i] for i in range(3)])
        else:
            # N-terminus: H points opposite to CA
            v = _normalize_vector([ca["x"] - n_atom["x"], ca["y"] - n_atom["y"], ca["z"] - n_atom["z"]])
            direction = [-v[0], -v[1], -v[2]]

        bond_len = 1.01  # N-H bond length in Ångströms
        new_h.append(
            {
                "record": "ATOM",
                "serial": 0,  # Will be renumbered
                "name": "H",
                "res_name": n_atom["res_name"],
                "chain": chain,
                "res_seq": res_seq,
                "x": n_atom["x"] + direction[0] * bond_len,
                "y": n_atom["y"] + direction[1] * bond_len,
                "z": n_atom["z"] + direction[2] * bond_len,
                "element": "H",
            }
        )
    return new_h


def _add_sidechain_oh(atoms: list[dict]) -> list[dict]:
    """Add hydrogens to Ser/Thr/Tyr OH groups."""
    donor_map = {"SER": "OG", "THR": "OG1", "TYR": "OH"}
    res_dict = {}
    for atom in atoms:
        key = (atom["chain"], atom["res_seq"], atom["res_name"])
        if key not in res_dict:
            res_dict[key] = {}
        res_dict[key][atom["name"]] = atom

    new_h = []
    for (chain, res_seq, res_name), res in res_dict.items():
        o_name = donor_map.get(res_name)
        if not o_name or o_name not in res:
            continue

        o_atom = res[o_name]
        anchor_name = "CB" if "CB" in res else "CA"
        if anchor_name not in res:
            continue

        anchor = res[anchor_name]
        direction = _normalize_vector(
            [o_atom["x"] - anchor["x"], o_atom["y"] - anchor["y"], o_atom["z"] - anchor["z"]]
        )

        new_h.append(
            {
                "record": "ATOM",
                "serial": 0,  # Will be renumbered
                "name": "H",
                "res_name": res_name,
                "chain": chain,
                "res_seq": res_seq,
                "x": o_atom["x"] + direction[0] * 0.96,
                "y": o_atom["y"] + direction[1] * 0.96,
                "z": o_atom["z"] + direction[2] * 0.96,
                "element": "H",
            }
        )
    return new_h


def convert_pdb_to_pdbqt(source: Path, destination: Path) -> Path:
    """Convert clean PDB to PDBQT with polar hydrogens."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Parse heavy atoms
    heavy_atoms = _parse_pdb_atoms(source)

    # Add polar hydrogens
    backbone_h = _add_backbone_nh(heavy_atoms)
    sidechain_h = _add_sidechain_oh(heavy_atoms)
    all_h = backbone_h + sidechain_h

    LOGGER.debug(f"Heavy atoms: {len(heavy_atoms)}, Backbone H: {len(backbone_h)}, Sidechain H: {len(sidechain_h)}")

    # Combine all atoms
    all_atoms = heavy_atoms + all_h

    # Write PDBQT
    lines = []
    for i, atom in enumerate(all_atoms, 1):
        elem = atom["element"].upper()
        ad_type = AD_ATOM_MAP.get(elem, "C")
        name = atom["name"].ljust(4)[:4]
        res = atom["res_name"].ljust(3)[:3]
        line = (
            f"ATOM  {i:5d} {name} {res} {atom['chain']}{atom['res_seq']:4d}    "
            f"{atom['x']:8.3f}{atom['y']:8.3f}{atom['z']:8.3f}"
            f"  1.00  0.00    {0.0:6.3f} {ad_type}\n"
        )
        lines.append(line)

    destination.write_text("".join(lines), encoding="utf-8")

    LOGGER.info(f"Converted PDB to PDBQT with {len(all_atoms)} atoms ({len(all_h)} polar hydrogens)")
    return destination

