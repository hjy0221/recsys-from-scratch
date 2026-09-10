"""Small, independently encodable user and item models."""

import torch
from torch import nn


class MatrixFactorization(nn.Module):
    def __init__(self, num_users: int, num_items: int, dimension: int = 16):
        super().__init__()
        self.users = nn.Embedding(num_users, dimension)
        self.items = nn.Embedding(num_items, dimension)
        nn.init.normal_(self.users.weight, std=0.1)
        nn.init.normal_(self.items.weight, std=0.1)
        self.register_buffer("mean", torch.tensor(0.0))

    def encode_users(self, ids: torch.Tensor) -> torch.Tensor:
        return self.users(ids)

    def encode_items(self, ids: torch.Tensor) -> torch.Tensor:
        return self.items(ids)

    def forward(self, users: torch.Tensor, items: torch.Tensor) -> torch.Tensor:
        return (self.encode_users(users) * self.encode_items(items)).sum(-1) + self.mean


class TwoTower(MatrixFactorization):
    def __init__(self, num_users: int, num_items: int, dimension: int = 16):
        super().__init__(num_users, num_items, dimension)
        self.user_tower = nn.Sequential(
            nn.Linear(dimension, dimension * 2), nn.ReLU(),
            nn.Linear(dimension * 2, dimension),
        )
        self.item_tower = nn.Sequential(
            nn.Linear(dimension, dimension * 2), nn.ReLU(),
            nn.Linear(dimension * 2, dimension),
        )

    def encode_users(self, ids: torch.Tensor) -> torch.Tensor:
        return self.user_tower(self.users(ids))

    def encode_items(self, ids: torch.Tensor) -> torch.Tensor:
        return self.item_tower(self.items(ids))
