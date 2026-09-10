from __future__ import annotations

from math import sqrt


def cosine_similarity(left: dict[int, float], right: dict[int, float]) -> float:
    if not left or not right:
        return 0.0

    common_item_ids = set(left).intersection(right)
    if not common_item_ids:
        return 0.0

    dot_product = sum(left[item_id] * right[item_id] for item_id in common_item_ids)
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot_product / (left_norm * right_norm)

