"""CPU training and portable checkpoints; external IDs never index embeddings."""

from dataclasses import asdict, dataclass
import math
from pathlib import Path

import torch

from src.data_loader import Rating
from src.models import MatrixFactorization, TwoTower


MODEL_TYPES = {"mf": MatrixFactorization, "two-tower": TwoTower}


@dataclass
class TrainedModel:
    model: MatrixFactorization
    algorithm: str
    dimension: int
    user_ids: list[int]
    item_ids: list[int]
    ratings: list[Rating]
    losses: list[float]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "version": 1, "algorithm": self.algorithm, "dimension": self.dimension,
            "user_ids": self.user_ids, "item_ids": self.item_ids,
            "ratings": [asdict(row) for row in self.ratings], "losses": self.losses,
            "state_dict": self.model.state_dict(),
        }, path)

    @classmethod
    def load(cls, path: str | Path) -> "TrainedModel":
        data = torch.load(path, map_location="cpu", weights_only=True)
        if data["version"] != 1:
            raise ValueError("Unsupported checkpoint version")
        model = MODEL_TYPES[data["algorithm"]](
            len(data["user_ids"]), len(data["item_ids"]), data["dimension"],
        )
        model.load_state_dict(data["state_dict"])
        model.eval()
        return cls(model, data["algorithm"], data["dimension"], data["user_ids"],
                   data["item_ids"], [Rating(**row) for row in data["ratings"]],
                   data["losses"])


def train_model(ratings: list[Rating], algorithm: str = "mf", epochs: int = 200,
                dimension: int = 16, learning_rate: float = 0.02,
                seed: int = 42) -> TrainedModel:
    if algorithm not in MODEL_TYPES:
        raise ValueError("algorithm must be mf or two-tower")
    if epochs < 1 or dimension < 1 or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("epochs, dimension and learning_rate must be positive")
    if not ratings or any(not math.isfinite(row.rating) for row in ratings):
        raise ValueError("Training requires nonempty, finite ratings")
    if len({(r.user_id, r.item_id) for r in ratings}) != len(ratings):
        raise ValueError("Duplicate user/item ratings must be aggregated before training")
    user_ids = sorted({row.user_id for row in ratings})
    item_ids = sorted({row.item_id for row in ratings})
    user_index = {value: index for index, value in enumerate(user_ids)}
    item_index = {value: index for index, value in enumerate(item_ids)}
    users = torch.tensor([user_index[row.user_id] for row in ratings])
    items = torch.tensor([item_index[row.item_id] for row in ratings])
    targets = torch.tensor([row.rating for row in ratings], dtype=torch.float32)
    with torch.random.fork_rng():
        torch.manual_seed(seed)
        model = MODEL_TYPES[algorithm](len(user_ids), len(item_ids), dimension)
    model.mean.copy_(targets.mean())
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    losses = []
    # Only observed entries contribute to the loss; missing ratings are not zero labels.
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(model(users, items), targets)
        if not torch.isfinite(loss):
            raise ValueError("Training diverged; reduce the learning rate")
        losses.append(loss.item())
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        losses.append(torch.nn.functional.mse_loss(model(users, items), targets).item())
    return TrainedModel(model, algorithm, dimension, user_ids, item_ids, ratings, losses)
