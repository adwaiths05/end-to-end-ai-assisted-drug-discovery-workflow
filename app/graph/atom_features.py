from __future__ import annotations

from rdkit import Chem


# Match the trained notebook artifact: atomic numbers 1..44 -> 44 slots.
# This keeps the total atom feature size at 56, which the saved GNN expects.
ATOM_TYPES = list(range(1, 45))
CHIRALITY_TYPES = [Chem.ChiralType.CHI_UNSPECIFIED, Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW]
HYBRIDIZATION_TYPES = [Chem.HybridizationType.SP, Chem.HybridizationType.SP2, Chem.HybridizationType.SP3, Chem.HybridizationType.SP3D, Chem.HybridizationType.SP3D2]


def one_hot(value, choices) -> list[int]:
    return [int(value == choice) for choice in choices]


def atom_features(atom: Chem.Atom) -> list[float]:
    features: list[float] = []
    features.extend(one_hot(atom.GetAtomicNum(), ATOM_TYPES))
    features.append(float(atom.GetDegree()))
    features.append(float(atom.GetFormalCharge()))
    features.append(float(atom.GetTotalNumHs()))
    features.append(float(atom.GetIsAromatic()))
    features.extend(one_hot(atom.GetChiralTag(), CHIRALITY_TYPES))
    features.extend(one_hot(atom.GetHybridization(), HYBRIDIZATION_TYPES))
    return features

