from __future__ import annotations

from dataclasses import dataclass

from src.data_loader import Rating
from src.metrics import cosine_similarity


UserItemMatrix = dict[int, dict[int, float]]


@dataclass(frozen=True)
class Recommendation:
    item_id: int
    score: float
    source: str


def build_user_item_matrix(ratings: list[Rating]) -> UserItemMatrix:
    matrix: UserItemMatrix = {}

    for row in ratings:
        matrix.setdefault(row.user_id, {})[row.item_id] = row.rating

    return matrix


def get_seen_items(matrix: UserItemMatrix, user_id: int) -> set[int]:
    return set(matrix.get(user_id, {}))


def recommend_popular(
    ratings: list[Rating],
    top_k: int,
    excluded_item_ids: set[int] | None = None,
) -> list[Recommendation]:
    excluded_item_ids = excluded_item_ids or set()
    stats: dict[int, tuple[float, int]] = {}

    for row in ratings:
        total, count = stats.get(row.item_id, (0.0, 0))
        stats[row.item_id] = (total + row.rating, count + 1)

    ranked = sorted(
        (
            Recommendation(
                item_id=item_id,
                score=total / count,
                source="popular",
            )
            for item_id, (total, count) in stats.items()
            if item_id not in excluded_item_ids
        ),
        key=lambda rec: (-rec.score, -stats[rec.item_id][1], rec.item_id),
    )

    return ranked[:top_k]


def find_similar_users(matrix: UserItemMatrix, user_id: int) -> list[tuple[int, float]]:
    target_vector = matrix.get(user_id, {})
    similarities: list[tuple[int, float]] = []

    for other_user_id, other_vector in matrix.items():
        if other_user_id == user_id:
            continue

        similarity = cosine_similarity(target_vector, other_vector)
        if similarity > 0.0:
            similarities.append((other_user_id, similarity))

    return sorted(similarities, key=lambda row: (-row[1], row[0]))


def recommend_user_based_cf(
    ratings: list[Rating],
    user_id: int,
    top_k: int,
    fallback_to_popular: bool = True,
) -> list[Recommendation]:
    matrix = build_user_item_matrix(ratings)
    seen_item_ids = get_seen_items(matrix, user_id)
    similar_users = find_similar_users(matrix, user_id)

    weighted_scores: dict[int, float] = {}
    similarity_sums: dict[int, float] = {}

    for neighbor_user_id, similarity in similar_users:
        for item_id, rating in matrix[neighbor_user_id].items():
            if item_id in seen_item_ids:
                continue

            weighted_scores[item_id] = weighted_scores.get(item_id, 0.0) + similarity * rating
            similarity_sums[item_id] = similarity_sums.get(item_id, 0.0) + similarity

    recommendations = sorted(
        (
            Recommendation(
                item_id=item_id,
                score=weighted_sum / similarity_sums[item_id],
                source="collaborative",
            )
            for item_id, weighted_sum in weighted_scores.items()
        ),
        key=lambda rec: (-rec.score, rec.item_id),
    )

    if not fallback_to_popular or len(recommendations) >= top_k:
        return recommendations[:top_k]

    already_recommended = {rec.item_id for rec in recommendations}
    excluded_item_ids = seen_item_ids.union(already_recommended)
    fallback = recommend_popular(
        ratings=ratings,
        top_k=top_k - len(recommendations),
        excluded_item_ids=excluded_item_ids,
    )

    return recommendations + fallback

