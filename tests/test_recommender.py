from __future__ import annotations

from src.data_loader import Rating
from src.metrics import cosine_similarity
from src.recommender import (
    build_user_item_matrix,
    find_similar_users,
    recommend_popular,
    recommend_user_based_cf,
)


def sample_ratings() -> list[Rating]:
    return [
        Rating(user_id=1, item_id=101, rating=5.0),
        Rating(user_id=1, item_id=102, rating=4.0),
        Rating(user_id=2, item_id=101, rating=4.0),
        Rating(user_id=2, item_id=103, rating=5.0),
        Rating(user_id=3, item_id=102, rating=5.0),
        Rating(user_id=3, item_id=103, rating=4.0),
    ]


def test_build_user_item_matrix_uses_sparse_representation() -> None:
    matrix = build_user_item_matrix(sample_ratings())

    assert matrix == {
        1: {101: 5.0, 102: 4.0},
        2: {101: 4.0, 103: 5.0},
        3: {102: 5.0, 103: 4.0},
    }


def test_cosine_similarity_uses_common_items_and_full_norms() -> None:
    left = {101: 5.0, 102: 4.0}
    right = {101: 4.0, 103: 5.0}

    similarity = cosine_similarity(left, right)

    assert round(similarity, 3) == 0.488


def test_popular_recommendations_exclude_seen_items() -> None:
    recommendations = recommend_popular(
        ratings=sample_ratings(),
        top_k=2,
        excluded_item_ids={101},
    )

    assert [rec.item_id for rec in recommendations] == [102, 103]
    assert all(rec.source == "popular" for rec in recommendations)


def test_find_similar_users_returns_ranked_positive_neighbors() -> None:
    matrix = build_user_item_matrix(sample_ratings())

    neighbors = find_similar_users(matrix, user_id=1)

    assert [user_id for user_id, _ in neighbors] == [2, 3]
    assert round(neighbors[0][1], 3) == round(neighbors[1][1], 3)


def test_user_based_cf_recommends_unseen_items() -> None:
    recommendations = recommend_user_based_cf(
        ratings=sample_ratings(),
        user_id=1,
        top_k=1,
    )

    assert len(recommendations) == 1
    assert recommendations[0].item_id == 103
    assert recommendations[0].source == "collaborative"


def test_user_based_cf_falls_back_to_popular_for_unknown_user() -> None:
    recommendations = recommend_user_based_cf(
        ratings=sample_ratings(),
        user_id=999,
        top_k=2,
    )

    assert [rec.source for rec in recommendations] == ["popular", "popular"]
    assert len(recommendations) == 2
