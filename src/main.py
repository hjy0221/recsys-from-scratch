from __future__ import annotations

import argparse
from pathlib import Path

from src.data_loader import Item, load_items, load_ratings
from src.recommender import Recommendation, recommend_user_based_cf, recommend_popular, build_user_item_matrix


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RATINGS_PATH = PROJECT_ROOT / "data" / "ratings.csv"
DEFAULT_ITEMS_PATH = PROJECT_ROOT / "data" / "items.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simple recommendations.")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--algorithm", choices=["popular", "cf", "mf", "two-tower", "faiss"], default="cf")
    parser.add_argument("--model-dir", type=Path, default=PROJECT_ROOT / "artifacts")
    parser.add_argument("--ratings-path", type=Path, default=DEFAULT_RATINGS_PATH)
    parser.add_argument("--items-path", type=Path, default=DEFAULT_ITEMS_PATH)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    return args


def format_recommendations(
    user_id: int,
    recommendations: list[Recommendation],
    items: dict[int, Item],
) -> str:
    lines = [
        f"Recommendations for user {user_id}",
        "",
        "rank  item_id  title                         score   source",
    ]

    for index, rec in enumerate(recommendations, start=1):
        title = items.get(rec.item_id).title if rec.item_id in items else "(unknown)"
        lines.append(
            f"{index:<5} {rec.item_id:<8} {title:<29} {rec.score:<7.3f} {rec.source}"
        )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ratings = load_ratings(args.ratings_path)
    items = load_items(args.items_path)
    if args.algorithm == "cf":
        recommendations = recommend_user_based_cf(ratings, args.user_id, args.top_k)
    elif args.algorithm == "popular":
        seen = set(build_user_item_matrix(ratings).get(args.user_id, {}))
        recommendations = recommend_popular(ratings, args.top_k, seen)
    else:
        from src.training import TrainedModel
        from src.retrieval import VectorRecommender

        algorithm = "two-tower" if args.algorithm == "faiss" else args.algorithm
        path = args.model_dir / f"{algorithm}.pt"
        if not path.exists():
            raise SystemExit("Model missing. Run: python -m src.train --algorithm all")
        trained = TrainedModel.load(path)
        if trained.algorithm != algorithm or trained.ratings != ratings:
            raise SystemExit("Checkpoint does not match algorithm/ratings. Retrain the model.")
        recommendations = VectorRecommender(trained).recommend(
            args.user_id, args.top_k, use_faiss=args.algorithm == "faiss",
        )

    print(format_recommendations(args.user_id, recommendations, items))


if __name__ == "__main__":
    main()
