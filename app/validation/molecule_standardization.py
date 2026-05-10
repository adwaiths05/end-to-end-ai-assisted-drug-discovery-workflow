from __future__ import annotations

from rdkit import Chem

try:
    from rdkit.Chem.MolStandardize import rdMolStandardize
except Exception:  # pragma: no cover
    rdMolStandardize = None


def standardize_molecule(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    if rdMolStandardize is not None:
        try:
            mol = rdMolStandardize.Normalize(mol)
            mol = rdMolStandardize.FragmentParent(mol)
            mol = rdMolStandardize.ChargeParent(mol)
            enumerator = rdMolStandardize.TautomerEnumerator()
            mol = enumerator.Canonicalize(mol)
        except Exception:
            pass
    return Chem.MolToSmiles(mol, canonical=True)

