"""Read-only serving: checkpoints and FAISS indexes are loaded once at startup."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.data_loader import Rating, load_items, load_ratings
from src.recommender import build_user_item_matrix, recommend_popular, recommend_user_based_cf
from src.retrieval import VectorRecommender
from src.training import TrainedModel
from src.discovery import DiscoveryCatalog


ROOT = Path(__file__).resolve().parents[1]
Algorithm = Literal["popular", "cf", "mf", "two-tower", "faiss"]


class RecommendationResult(BaseModel):
    item_id: int
    title: str
    score: float
    source: str


class RecommendationResponse(BaseModel):
    user_id: int
    algorithm: Algorithm
    recommendations: list[RecommendationResult]


class PersonalRating(BaseModel):
    item_id: int
    rating: int = Field(ge=1, le=5)


class DiscoveryRequest(BaseModel):
    ratings: list[PersonalRating] = Field(default_factory=list, max_length=1000)


def create_app(data_dir: Path | None = None, model_dir: Path | None = None) -> FastAPI:
    data_dir = Path(data_dir or os.getenv("RECSYS_DATA_DIR", ROOT / "data"))
    model_dir = Path(model_dir or os.getenv("RECSYS_MODEL_DIR", ROOT / "artifacts"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ratings = load_ratings(data_dir / "ratings.csv")
        app.state.items = load_items(data_dir / "items.csv")
        app.state.matrix = build_user_item_matrix(app.state.ratings)
        app.state.discovery = DiscoveryCatalog(data_dir) if (data_dir / "catalog.json").exists() else None
        app.state.models = {}
        for algorithm in ("mf", "two-tower"):
            path = model_dir / f"{algorithm}.pt"
            if path.exists():
                trained = TrainedModel.load(path)
                if trained.algorithm != algorithm or trained.ratings != app.state.ratings:
                    raise ValueError(f"Stale or mismatched checkpoint: {path}; retrain first")
                app.state.models[algorithm] = VectorRecommender(trained)
        yield
        app.state.models.clear()

    app = FastAPI(title="recsys-from-scratch", version="0.2.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=ROOT / "src/web"), name="static")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(ROOT / "src/web/index.html")

    @app.get("/catalog")
    def catalog():
        if app.state.discovery:
            return {"items": app.state.discovery.items, "sample_users": 600, "sample_ratings": 24000}
        return {"items": [
            {"item_id": item.item_id, "title": item.title, "category": item.category,
             "average": round(sum(r.rating for r in app.state.ratings if r.item_id == item.item_id)
                              / max(1, sum(r.item_id == item.item_id for r in app.state.ratings)), 1),
             "count": sum(r.item_id == item.item_id for r in app.state.ratings)}
            for item in app.state.items.values()
        ]}

    @app.post("/discover")
    def discover(body: DiscoveryRequest):
        ids = [r.item_id for r in body.ratings]
        allowed = app.state.discovery.by_id if app.state.discovery else app.state.items
        if len(ids) != len(set(ids)) or any(i not in allowed for i in ids):
            raise HTTPException(422, "Unknown or duplicate item")
        if app.state.discovery:
            return {"recommendations": app.state.discovery.recommend(body.ratings)}
        personal_id = min([0, *app.state.matrix]) - 1
        ratings = app.state.ratings + [Rating(personal_id, r.item_id, r.rating) for r in body.ratings]
        results = recommend_user_based_cf(ratings, personal_id, len(app.state.items))
        return {"recommendations": [
            {"item_id": rec.item_id, "score": rec.score,
             "reason": "비슷한 취향의 학습자가 높게 평가했어요" if rec.source == "collaborative"
                       else "샘플 학습자들의 평점이 높은 강좌예요"}
            for rec in results
        ]}

    @app.get("/health")
    def health() -> dict:
        algorithms = ["popular", "cf", *app.state.models]
        if "two-tower" in app.state.models:
            algorithms.append("faiss")
        return {"status": "ok", "algorithms": algorithms}

    @app.get("/recommendations", response_model=RecommendationResponse)
    def recommendations(user_id: int, top_k: int = Query(3, ge=1, le=100),
                        algorithm: Algorithm = "cf") -> RecommendationResponse:
        if algorithm == "popular":
            seen = set(app.state.matrix.get(user_id, {}))
            results = recommend_popular(app.state.ratings, top_k, seen)
        elif algorithm == "cf":
            results = recommend_user_based_cf(app.state.ratings, user_id, top_k)
        else:
            key = "two-tower" if algorithm == "faiss" else algorithm
            if key not in app.state.models:
                raise HTTPException(503, "Model missing. Run python -m src.train and restart API.")
            results = app.state.models[key].recommend(user_id, top_k, algorithm == "faiss")
        return RecommendationResponse(
            user_id=user_id, algorithm=algorithm,
            recommendations=[RecommendationResult(
                item_id=rec.item_id,
                title=app.state.items[rec.item_id].title if rec.item_id in app.state.items else "(unknown)",
                score=rec.score, source=rec.source,
            ) for rec in results],
        )

    return app


app = create_app()
