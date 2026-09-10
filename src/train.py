import argparse
from pathlib import Path

from src.data_loader import load_ratings
from src.training import train_model


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and save recommendation models.")
    parser.add_argument("--algorithm", choices=["mf", "two-tower", "all"], default="all")
    parser.add_argument("--ratings-path", type=Path, default=ROOT / "data/ratings.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--dimension", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        ratings = load_ratings(args.ratings_path)
        algorithms = ["mf", "two-tower"] if args.algorithm == "all" else [args.algorithm]
        for algorithm in algorithms:
            trained = train_model(ratings, algorithm, args.epochs, args.dimension,
                                  args.learning_rate, args.seed)
            path = args.output_dir / f"{algorithm}.pt"
            trained.save(path)
            print(f"{algorithm}: training MSE {trained.losses[0]:.6f} -> "
                  f"{trained.losses[-1]:.6f}; saved {path}")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
