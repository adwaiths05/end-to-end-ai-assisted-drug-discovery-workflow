from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, GINEConv, NNConv, global_max_pool, global_mean_pool


class GraphStructureLearning(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.project = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.gate = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.Sigmoid())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        project_layer = getattr(self, "project", None)
        if project_layer is None:
            project_layer = getattr(self, "similarity_proj", None)
        if project_layer is None:
            raise AttributeError("GraphStructureLearning is missing both 'project' and 'similarity_proj'")
        
        projected = project_layer(x)
        
        # Check if gate is actually a Linear layer with in_features=512 (compatibility hack)
        if isinstance(self.gate, nn.Linear) and self.gate.in_features == 512:
            # Loaded model expects [x, projected] concatenated
            gate_val = torch.sigmoid(self.gate(torch.cat([x, projected], dim=-1)))
        else:
            gate_val = self.gate(x)
            
        return gate_val * projected + (1.0 - gate_val) * x


class GINBlock(nn.Module):
    """Single GINEConv layer with batch normalization and residual connection."""
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int) -> None:
        super().__init__()
        mlp = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.conv = GINEConv(nn=mlp, train_eps=True, edge_dim=edge_dim)
        self.bn = nn.BatchNorm1d(hidden_dim)
        self.residual_proj = (
            nn.Linear(node_dim, hidden_dim, bias=False)
            if node_dim != hidden_dim
            else nn.Identity()
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        return F.relu(self.bn(self.conv(x, edge_index, edge_attr))) + self.residual_proj(x)


class EdgeAwareMPNN(nn.Module):
    def __init__(self, node_dim: int = 57, edge_dim: int = 9, hidden_dim: int = 256) -> None:
        super().__init__()
        self.node_encoder = nn.Linear(node_dim, hidden_dim)
        self.gsl = GraphStructureLearning(hidden_dim)
        edge_mlp = nn.Sequential(
            nn.Linear(edge_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim * hidden_dim),
        )
        self.conv1 = NNConv(hidden_dim, hidden_dim, edge_mlp, aggr="mean")
        self.conv2 = NNConv(hidden_dim, hidden_dim, edge_mlp, aggr="mean")
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.attention = GATConv(hidden_dim, hidden_dim, heads=4, concat=False, dropout=0.2)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
        )

    def forward(self, data) -> torch.Tensor:
        x = self.node_encoder(data.x.float())
        x = self.gsl(x)
        residual = x
        x = F.relu(self.bn1(self.conv1(x, data.edge_index, data.edge_attr.float())))
        x = x + residual
        residual = x
        x = F.relu(self.bn2(self.conv2(x, data.edge_index, data.edge_attr.float())))
        x = x + residual
        x = self.attention(x, data.edge_index)
        pooled = torch.cat([global_mean_pool(x, data.batch), global_max_pool(x, data.batch)], dim=1)
        return self.head(pooled).squeeze(-1)


class GINModel(nn.Module):
    """5-layer GINEConv with GSL, 8-head GAT, dual readout, regression head."""
    def __init__(self, node_dim: int = 56, edge_dim: int = 9, hidden_dim: int = 256, n_layers: int = 5, gat_heads: int = 8, dropout: float = 0.3) -> None:
        super().__init__()
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
        )
        self.edge_encoder = nn.Linear(edge_dim, hidden_dim)
        self.gsl = GraphStructureLearning(hidden_dim)
        self.gin_layers = nn.ModuleList([
            GINBlock(hidden_dim, hidden_dim, hidden_dim) for _ in range(n_layers)
        ])
        self.attention = GATConv(
            hidden_dim,
            hidden_dim // gat_heads,
            heads=gat_heads,
            concat=True,
            dropout=dropout,
        )
        readout_dim = 2 * hidden_dim
        self.head = nn.Sequential(
            nn.Linear(readout_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
        )

    def forward(self, data) -> torch.Tensor:
        x = self.node_encoder(data.x.float())
        edge_attr = F.relu(self.edge_encoder(data.edge_attr.float()))
        x = self.gsl(x)
        for layer in self.gin_layers:
            x = layer(x, data.edge_index, edge_attr)
        x = F.relu(self.attention(x, data.edge_index))
        pooled = torch.cat([global_mean_pool(x, data.batch), global_max_pool(x, data.batch)], dim=1)
        return self.head(pooled).squeeze(-1)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    filename: str
