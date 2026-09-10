from pathlib import Path

import numpy as np
import pytest
import torch

from src.data_loader import Rating, load_ratings
from src.retrieval import VectorRecommender
from src.training import TrainedModel, train_model


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", params=["mf", "two-tower"])
def trained(request):
    return train_model(load_ratings(ROOT / "data/ratings.csv"), request.param)


def test_training_reduces_observed_rating_loss(trained):
    assert np.isfinite(trained.losses).all()
    assert trained.losses[-1] < trained.losses[0] * 0.1


def test_checkpoint_round_trip(trained, tmp_path):
    path = tmp_path / "model.pt"
    trained.save(path)
    restored = TrainedModel.load(path)
    expected = VectorRecommender(trained).recommend(1)
    assert VectorRecommender(restored).recommend(1) == expected
    assert restored.user_ids == trained.user_ids
    assert restored.item_ids == trained.item_ids


def test_faiss_matches_direct_scores_and_excludes_seen(trained):
    recommender = VectorRecommender(trained)
    for user_id in trained.user_ids:
        direct = recommender.recommend(user_id, 100)
        indexed = recommender.recommend(user_id, 100, use_faiss=True)
        assert [r.item_id for r in indexed] == [r.item_id for r in direct]
        assert [r.score for r in indexed] == pytest.approx([r.score for r in direct], abs=1e-5)
        assert not set(r.item_id for r in indexed) & set(recommender.seen[user_id])
        assert len(recommender.recommend(user_id, 2, True)) == 2


def test_unknown_user_and_invalid_k(trained):
    recommender = VectorRecommender(trained)
    assert all(r.source == "popular" for r in recommender.recommend(999, 3, True))
    with pytest.raises(ValueError):
        recommender.recommend(1, 0)


def test_non_contiguous_ids_and_fully_seen_user():
    trained = train_model([Rating(500, 9000, 4), Rating(500, 12345, 5)], epochs=2)
    assert trained.user_ids == [500]
    assert trained.item_ids == [9000, 12345]
    assert VectorRecommender(trained).recommend(500, 3, True) == []


@pytest.mark.parametrize("ratings", [[], [Rating(1, 1, float("nan"))],
                                     [Rating(1, 1, 4), Rating(1, 1, 5)]])
def test_invalid_training_data(ratings):
    with pytest.raises(ValueError):
        train_model(ratings)


def test_seed_is_reproducible():
    ratings = load_ratings(ROOT / "data/ratings.csv")
    a = train_model(ratings, epochs=5)
    b = train_model(ratings, epochs=5)
    assert a.losses == b.losses
    for key, value in a.model.state_dict().items():
        torch.testing.assert_close(value, b.model.state_dict()[key])
