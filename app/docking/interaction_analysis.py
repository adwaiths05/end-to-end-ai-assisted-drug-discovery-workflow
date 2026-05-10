from __future__ import annotations

import logging
import re
from pathlib import Path

LOGGER = logging.getLogger(__name__)

# Atom properties for H-bond detection
DONOR_ATOMS = {"N", "O", "S"}  # atoms that can donate H
ACCEPTOR_ATOMS = {"N", "O", "F", "S"}

HB_DIST_CUT = 3.5  # Angstroms — standard H-bond distance cutoff
CONTACT_CUT = 4.5  # Angstroms — hydrophobic/vdW contact cutoff


class InteractionAnalyzer:
    """Analyze protein-ligand interactions from docked poses."""

    def __init__(self, receptor_pdbqt: Path) -> None:
        self.receptor_pdbqt = receptor_pdbqt
        self.receptor_atoms = self._parse_receptor()

    def _parse_receptor(self) -> list[dict]:
        """Parse receptor PDBQT to extract atom coordinates and properties."""
        atoms = []
        try:
            with open(self.receptor_pdbqt) as f:
                for line in f:
                    if not line.startswith("ATOM"):
                        continue
                    try:
                        atom = {
                            "res_name": line[17:20].strip(),
                            "chain": line[21].strip(),
                            "res_seq": int(line[22:26]),
                            "atom_name": line[12:16].strip(),
                            "x": float(line[30:38]),
                            "y": float(line[38:46]),
                            "z": float(line[46:54]),
                            "element": line[76:78].strip() if len(line) > 77 else "",
                        }
                        atoms.append(atom)
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            LOGGER.error(f"Error parsing receptor: {e}")

        return atoms

    def _parse_ligand_pose(self, pose_pdbqt: Path) -> list[dict]:
        """Parse ligand pose PDBQT (first MODEL only)."""
        atoms = []
        try:
            in_model = False
            with open(pose_pdbqt) as f:
                for line in f:
                    if line.startswith("MODEL"):
                        in_model = True
                    if line.startswith("ENDMDL"):
                        break
                    if in_model and line.startswith(("ATOM", "HETATM")):
                        try:
                            atom = {
                                "atom_name": line[12:16].strip(),
                                "x": float(line[30:38]),
                                "y": float(line[38:46]),
                                "z": float(line[46:54]),
                                "element": line[76:78].strip() if len(line) > 77 else "",
                            }
                            atoms.append(atom)
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            LOGGER.warning(f"Error parsing ligand pose: {e}")

        return atoms

    @staticmethod
    def _distance(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2) ** 0.5

    @staticmethod
    def _get_element(atom_name: str) -> str:
        """Extract element symbol from atom name."""
        return re.sub(r"[0-9]", "", atom_name)[0].upper() if atom_name else "C"

    def find_hbonds(self, lig_atoms: list[dict]) -> list[dict]:
        """Find hydrogen bonds between ligand and receptor."""
        hbonds = []

        for l_atom in lig_atoms:
            l_elem = self._get_element(l_atom.get("element") or l_atom["atom_name"])
            l_pos = (l_atom["x"], l_atom["y"], l_atom["z"])

            for r_atom in self.receptor_atoms:
                r_elem = self._get_element(r_atom.get("element") or r_atom["atom_name"])
                r_pos = (r_atom["x"], r_atom["y"], r_atom["z"])

                dist = self._distance(l_pos, r_pos)

                if dist < HB_DIST_CUT:
                    # Check donor-acceptor compatibility
                    if (l_elem in DONOR_ATOMS and r_elem in ACCEPTOR_ATOMS) or (
                        r_elem in DONOR_ATOMS and l_elem in ACCEPTOR_ATOMS
                    ):
                        hbonds.append(
                            {
                                "ligand_atom": l_atom["atom_name"],
                                "receptor_residue": f"{r_atom['res_name']}{r_atom['res_seq']}",
                                "receptor_atom": r_atom["atom_name"],
                                "distance": round(dist, 2),
                            }
                        )

        return hbonds

    def find_contacts(self, lig_atoms: list[dict]) -> dict[str, float]:
        """Find close contacts (within 4.5 Å) and return key residues."""
        contacts = {}  # {residue_key: min_distance}

        for l_atom in lig_atoms:
            l_pos = (l_atom["x"], l_atom["y"], l_atom["z"])

            for r_atom in self.receptor_atoms:
                r_pos = (r_atom["x"], r_atom["y"], r_atom["z"])
                dist = self._distance(l_pos, r_pos)

                if dist < CONTACT_CUT:
                    key = f"{r_atom['res_name']}{r_atom['res_seq']}"
                    if key not in contacts or dist < contacts[key]:
                        contacts[key] = round(dist, 2)

        return contacts

    def analyze_pose(
        self, ligand_id: str, smiles: str, affinity: float, pose_pdbqt: Path
    ) -> dict:
        """Analyze a single docked pose."""
        lig_atoms = self._parse_ligand_pose(pose_pdbqt)

        if not lig_atoms:
            LOGGER.warning(f"No atoms found in ligand pose: {pose_pdbqt}")
            return {
                "ligand_id": ligand_id,
                "smiles": smiles,
                "affinity": affinity,
                "n_hbonds": 0,
                "n_contacts": 0,
                "key_residues": [],
                "hbonds": [],
                "top_contacts": {},
            }

        hbonds = self.find_hbonds(lig_atoms)
        contacts = self.find_contacts(lig_atoms)

        # Get top 6 contacting residues
        top_contacts = dict(sorted(contacts.items(), key=lambda x: x[1])[:6])

        # Format key residues as list
        key_residues = [f"{res}({dist:.1f}Å)" for res, dist in top_contacts.items()]

        return {
            "ligand_id": ligand_id,
            "smiles": smiles,
            "affinity": affinity,
            "n_hbonds": len(hbonds),
            "n_contacts": len(contacts),
            "key_residues": key_residues,
            "hbonds": hbonds,
            "top_contacts": top_contacts,
        }
