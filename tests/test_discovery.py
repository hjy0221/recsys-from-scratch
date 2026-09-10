from fastapi.testclient import TestClient
import pytest

from src.api import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(model_dir=tmp_path)) as client:
        yield client


def test_personal_ratings_change_recommendations_without_mutating_sample(client):
    initial = client.post("/discover", json={"ratings": []}).json()
    response = client.post("/discover", json={"ratings": [{"item_id": 101, "rating": 5}]})
    assert response.status_code == 200
    results = response.json()["recommendations"]
    assert len(results) == 307
    assert 101 not in {r["item_id"] for r in results}
    assert any("취향" in r["reason"] for r in results)
    assert client.post("/discover", json={"ratings": []}).json() == initial


@pytest.mark.parametrize("ratings", [
    [{"item_id": 101, "rating": 0}], [{"item_id": 101, "rating": 6}],
    [{"item_id": 999, "rating": 5}],
    [{"item_id": 101, "rating": 4}, {"item_id": 101, "rating": 5}],
])
def test_invalid_personal_ratings(client, ratings):
    assert client.post("/discover", json={"ratings": ratings}).status_code == 422


def test_all_rated_returns_empty(client):
    ratings = [{"item_id": i["item_id"], "rating": 4} for i in client.get("/catalog").json()["items"]]
    assert client.post("/discover", json={"ratings": ratings}).json() == {"recommendations": []}


def test_catalog_and_local_assets(client):
    catalog = client.get("/catalog").json()["items"]
    assert len(catalog) == 308
    assert len({i["category"] for i in catalog}) == 5
    assert all(1 <= item["average"] <= 5 and item["count"] > 0 for item in catalog)
    assert "NEXT" in client.get("/").text
    for path in ("app.js", "style.css", "lucide.min.js", "images/code.jpg", "images/desk.jpg", "images/data.jpg"):
        response = client.get(f"/static/{path}")
        assert response.status_code == 200
        assert len(response.content) > 100


def test_opposing_tastes_change_top_recommendations(client):
    catalog = client.get("/catalog").json()["items"]
    lookup = {i["item_id"]: i for i in catalog}
    liked = client.post("/discover", json={"ratings": [{"item_id": 1000, "rating": 5}]}).json()["recommendations"]
    disliked = client.post("/discover", json={"ratings": [{"item_id": 1000, "rating": 1}]}).json()["recommendations"]
    liked_genres = [lookup[r["item_id"]]["genre"] for r in liked[:20]]
    disliked_genres = [lookup[r["item_id"]]["genre"] for r in disliked[:20]]
    assert liked_genres.count("SF·테크") > disliked_genres.count("SF·테크")
    assert len({lookup[r["item_id"]]["category"] for r in liked[:20]}) >= 3


def test_dataset_integrity(client):
    catalog = client.get("/catalog").json()
    assert catalog["sample_users"] == 600
    assert catalog["sample_ratings"] == 24000
    assert len({i["title"] for i in catalog["items"]}) == 308
    assert len({i["item_id"] for i in catalog["items"]}) == 308
    assert all(i["fictional"] for i in catalog["items"])
    for image in {i["image"] for i in catalog["items"]}:
        assert client.get(f"/static/images/{image}.jpg").status_code == 200
