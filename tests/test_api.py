from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from src.api import create_app
from src.data_loader import Rating, load_ratings
from src.training import train_model


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def model_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("models")
    for algorithm in ("mf", "two-tower"):
        train_model(load_ratings(ROOT / "data/ratings.csv"), algorithm, epochs=20).save(
            directory / f"{algorithm}.pt")
    return directory


@pytest.mark.parametrize("algorithm", ["popular", "cf", "mf", "two-tower", "faiss"])
def test_api_recommendations_and_cli(algorithm, model_dir):
    with TestClient(create_app(model_dir=model_dir)) as client:
        response = client.get("/recommendations", params={"user_id": 1, "top_k": 3, "algorithm": algorithm})
        assert response.status_code == 200
        results = response.json()["recommendations"]
        assert len(results) == 3
        assert not {r["item_id"] for r in results} & {101, 102, 103}
        assert all(r["title"] != "(unknown)" for r in results)
        assert algorithm in client.get("/health").json()["algorithms"]
        unknown = client.get("/recommendations", params={"user_id": 999, "algorithm": algorithm})
        assert all(r["source"] == "popular" for r in unknown.json()["recommendations"])
    run = subprocess.run([sys.executable, "-m", "src.main", "--user-id", "1",
                          "--algorithm", algorithm, "--model-dir", str(model_dir)],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert "Recommendations for user 1" in run.stdout
    assert len(run.stdout.strip().splitlines()) == 6


@pytest.mark.parametrize("params", [{"user_id": 1, "top_k": 0}, {"user_id": 1, "top_k": 101},
                                    {"user_id": "abc"}, {"user_id": 1, "algorithm": "bad"}, {}])
def test_api_validation(params, model_dir):
    with TestClient(create_app(model_dir=model_dir)) as client:
        assert client.get("/recommendations", params=params).status_code == 422


def test_missing_models_return_503_without_disabling_baselines(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        assert client.get("/recommendations?user_id=1&algorithm=faiss").status_code == 503
        assert client.get("/recommendations?user_id=1").status_code == 200


def test_stale_checkpoint_is_rejected(tmp_path):
    train_model([Rating(1, 101, 1)], epochs=1).save(tmp_path / "mf.pt")
    with pytest.raises(ValueError, match="Stale"):
        with TestClient(create_app(model_dir=tmp_path)):
            pass
