from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem

LOGGER = logging.getLogger(__name__)


def smiles_to_sdf(smiles: str, destination: Path, seed: int = 42) -> Path | None:
    """Convert SMILES to 3D SDF with geometry optimization.
    
    Steps:
    1. Parse SMILES to RDKit mol
    2. Add hydrogens
    3. Generate 3D coordinates (ETKDG v3, fallback to ETKDG)
    4. Optimize with MMFF94 force field
    5. Write to SDF
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        LOGGER.warning(f"Invalid SMILES: {smiles}")
        return None

    try:
        mol = Chem.AddHs(mol)

        # Try ETKDG v3 first (best quality)
        params = AllChem.ETKDGv3()
        params.randomSeed = seed
        embed_result = AllChem.EmbedMolecule(mol, params)

        # Fallback to standard ETKDG if v3 fails
        if embed_result == -1:
            LOGGER.debug(f"ETKDGv3 failed for {smiles}, trying standard ETKDG")
            embed_result = AllChem.EmbedMolecule(mol, AllChem.ETKDG())

        if embed_result == -1:
            LOGGER.warning(f"Failed to generate 3D coordinates for {smiles}")
            return None

        # Geometry optimization with MMFF94
        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
        except Exception as e:
            LOGGER.debug(f"MMFF optimization failed for {smiles}: {e}")
            # Continue anyway — 3D coords are more important than optimization

        # Write SDF
        destination.parent.mkdir(parents=True, exist_ok=True)
        writer = Chem.SDWriter(str(destination))
        writer.write(mol)
        writer.close()

        LOGGER.debug(f"Generated SDF: {destination}")
        return destination

    except Exception as e:
        LOGGER.error(f"Error generating SDF for {smiles}: {e}")
        return None


def sdf_to_pdbqt(sdf_path: Path, destination: Path) -> Path:
    """Convert SDF to PDBQT via meeko, with fallback to obabel.
    
    Try order:
    1. Meeko (preferred — better parameters)
    2. Obabel (fallback)
    3. Manual conversion (last resort)
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: Try OpenBabel Python bindings (Preferred by user)
    try:
        from openbabel import openbabel

        obConversion = openbabel.OBConversion()
        obConversion.SetInAndOutFormats("sdf", "pdbqt")

        mol = openbabel.OBMol()
        if not obConversion.ReadFile(mol, str(sdf_path)):
            raise ValueError(f"OpenBabel could not read SDF: {sdf_path}")

        # Add partial charges (Gasteiger) typically required for docking
        charge_model = openbabel.OBChargeModel.FindType("gasteiger")
        if charge_model:
            charge_model.ComputeCharges(mol)

        if not obConversion.WriteFile(mol, str(destination)):
            raise RuntimeError(f"OpenBabel could not write PDBQT: {destination}")

        LOGGER.info(f"Converted SDF to PDBQT via OpenBabel Python API: {destination}")
        return destination
    except Exception as e:
        LOGGER.debug(f"OpenBabel Python API conversion failed: {e}, trying Meeko")

    # Strategy 2: Try meeko (0.7.x API)
    try:
        from meeko import MoleculePreparation, PDBQTWriterLegacy

        mol = Chem.SDMolSupplier(str(sdf_path), removeHs=False)[0]
        if mol is None:
            raise ValueError("Unable to read ligand SDF")

        preparator = MoleculePreparation()
        mol_setups = preparator.prepare(mol)   # returns list of MoleculeSetup

        if not mol_setups:
            raise ValueError("meeko returned no setups")

        pdbqt_string, is_ok, error_msg = PDBQTWriterLegacy.write_string(mol_setups[0])
        if not is_ok:
            raise RuntimeError(f"meeko PDBQT write failed: {error_msg}")

        destination.write_text(pdbqt_string, encoding="utf-8")
        LOGGER.info(f"Converted SDF to PDBQT via meeko: {destination}")
        return destination

    except Exception as e:
        LOGGER.debug(f"Meeko conversion failed: {e}, using manual conversion")

    # Strategy 3: Manual conversion (RDKit-based, no external tools needed)
    try:
        supplier = Chem.SDMolSupplier(str(sdf_path), removeHs=False)
        mol = supplier[0] if supplier and len(supplier) else None
        if mol is None:
            raise RuntimeError(f"Unable to read ligand SDF: {sdf_path}")

        conformer = mol.GetConformer()
        lines = ["ROOT"]

        for atom in mol.GetAtoms():
            position = conformer.GetAtomPosition(atom.GetIdx())
            element = atom.GetSymbol().upper()
            line = (
                f"ATOM  {atom.GetIdx() + 1:5d} {element:<4s} LIG A{1:4d}"
                f"    {position.x:8.3f}{position.y:8.3f}{position.z:8.3f}  {0.0:6.3f} {element:>2s}"
            )
            lines.append(line)

        lines.append("ENDROOT")
        lines.append("TORSDOF 0")

        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
        LOGGER.debug(f"Converted SDF to PDBQT via manual conversion: {destination}")
        return destination

    except Exception as e:
        LOGGER.error(f"All PDBQT conversion strategies failed for {sdf_path}: {e}")
        raise RuntimeError(f"Failed to convert {sdf_path} to PDBQT") from e

