from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rating:
    user_id: int
    item_id: int
    rating: float


@dataclass(frozen=True)
class Item:
    item_id: int
    title: str
    category: str


def load_ratings(path: str | Path) -> list[Rating]:
    ratings_path = Path(path)
    ratings: list[Rating] = []

    with ratings_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ratings.append(
                Rating(
                    user_id=int(row["user_id"]),
                    item_id=int(row["item_id"]),
                    rating=float(row["rating"]),
                )
            )

    return ratings


def load_items(path: str | Path) -> dict[int, Item]:
    items_path = Path(path)
    items: dict[int, Item] = {}

    with items_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            item = Item(
                item_id=int(row["item_id"]),
                title=row["title"],
                category=row["category"],
            )
            items[item.item_id] = item

    return items

