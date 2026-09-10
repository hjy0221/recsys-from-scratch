"""Personalized shelves: centered neighbors, content taste and Bayesian popularity."""

from collections import defaultdict
import json
import math

from src.data_loader import load_ratings
from src.recommender import build_user_item_matrix


class DiscoveryCatalog:
    def __init__(self, data_dir):
        self.items = json.loads((data_dir / "catalog.json").read_text(encoding="utf-8"))
        self.by_id = {i["item_id"]: i for i in self.items}
        rows = load_ratings(data_dir / "discovery_ratings.csv")
        self.matrix = build_user_item_matrix(rows)
        stats = defaultdict(list)
        for r in rows:
            stats[r.item_id].append(r.rating)
        mean = sum(r.rating for r in rows)/len(rows)
        self.popularity = {}
        for item in self.items:
            values = stats[item["item_id"]]
            item.update(average=round(sum(values)/len(values), 1) if values else 0, count=len(values))
            self.popularity[item["item_id"]] = (sum(values)+20*mean)/(len(values)+20)

    def recommend(self, ratings):
        personal = {r.item_id: r.rating for r in ratings}
        genre_taste, type_taste = defaultdict(list), defaultdict(list)
        for item_id, value in personal.items():
            item = self.by_id[item_id]
            genre_taste[item["genre"]].append(value-3)
            type_taste[item["category"]].append(value-3)
        weighted, weights = defaultdict(float), defaultdict(float)
        # Center around neutral (3): disliked content should not act as a positive preference.
        target = {i: r-3 for i, r in personal.items()}
        norm = math.sqrt(sum(r*r for r in target.values()))
        for neighbor in self.matrix.values():
            common = target.keys() & neighbor.keys()
            denominator = norm * math.sqrt(sum((r-3)**2 for r in neighbor.values()))
            similarity = sum(target[i]*(neighbor[i]-3) for i in common)/denominator if denominator else 0
            similarity *= len(common)/(len(common)+2)
            if similarity <= 0:
                continue
            for item_id, value in neighbor.items():
                if item_id not in personal:
                    weighted[item_id] += similarity*(value-3)
                    weights[item_id] += similarity
        results = []
        for item in self.items:
            item_id = item["item_id"]
            if item_id in personal:
                continue
            genre_values, type_values = genre_taste[item["genre"]], type_taste[item["category"]]
            genre_affinity = sum(genre_values)/(len(genre_values)+1)
            type_affinity = sum(type_values)/(len(type_values)+2)
            neighbor_score = weighted[item_id]/weights[item_id] if weights[item_id] else 0
            score = self.popularity[item_id] + 0.8*genre_affinity + 0.35*type_affinity + 0.35*neighbor_score
            reason = (f"좋아한 {item['genre']} 콘텐츠와 같은 취향" if genre_affinity > 0
                      else "비슷한 취향의 사람들이 높게 평가했어요" if neighbor_score > 0.3
                      else "샘플 평점과 평가 수를 함께 반영한 추천")
            results.append(dict(item_id=item_id, score=round(score, 6), reason=reason))
        return sorted(results, key=lambda r: (-r["score"], r["item_id"]))
