from __future__ import annotations

from rdkit import Chem
import torch
from torch_geometric.data import Data

from app.graph.atom_features import atom_features
from app.graph.bond_features import bond_features


def smiles_to_graph(smiles: str, label: float | None = None) -> Data | None:
    mol = Chem.MolFromSmiles(str(smiles))
    if mol is None:
        return None

    node_matrix = [atom_features(atom) for atom in mol.GetAtoms()]
    edge_index: list[list[int]] = []
    edge_attr: list[list[float]] = []

    for bond in mol.GetBonds():
        begin = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        bf = bond_features(bond)
        edge_index.extend([[begin, end], [end, begin]])
        edge_attr.extend([bf, bf])

    if not edge_index:
        return None

    data = Data(
        x=torch.tensor(node_matrix, dtype=torch.float32),
        edge_index=torch.tensor(edge_index, dtype=torch.long).t().contiguous(),
        edge_attr=torch.tensor(edge_attr, dtype=torch.float32),
    )
    if label is not None:
        data.y = torch.tensor([float(label)], dtype=torch.float32)
    return data

