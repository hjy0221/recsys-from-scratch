"""Exact dot-product retrieval, optionally backed by a reusable FAISS index."""

import faiss
import numpy as np
import torch

from src.recommender import Recommendation, build_user_item_matrix, recommend_popular
from src.training import TrainedModel


class VectorRecommender:
    def __init__(self, trained: TrainedModel):
        self.trained = trained
        self.user_index = {uid: index for index, uid in enumerate(trained.user_ids)}
        self.seen = build_user_item_matrix(trained.ratings)
        with torch.inference_mode():
            self.vectors = trained.model.encode_items(
                torch.arange(len(trained.item_ids)),
            ).numpy().astype("float32")
        self.index = faiss.IndexFlatIP(self.vectors.shape[1])
        self.index.add(np.ascontiguousarray(self.vectors))

    def recommend(self, user_id: int, top_k: int = 3,
                  use_faiss: bool = False) -> list[Recommendation]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if user_id not in self.user_index:
            return recommend_popular(self.trained.ratings, top_k)
        with torch.inference_mode():
            query = self.trained.model.encode_users(
                torch.tensor([self.user_index[user_id]]),
            ).numpy().astype("float32")
        if use_faiss:
            # Retrieve all for deterministic ties and seen-item filtering in this small demo.
            scores, indices = self.index.search(query, len(self.trained.item_ids))
            pairs = zip(indices[0].tolist(), scores[0].tolist())
        else:
            pairs = enumerate((self.vectors @ query[0]).tolist())
        source = self.trained.algorithm + ("-faiss" if use_faiss else "")
        results = [
            Recommendation(self.trained.item_ids[index], score + self.trained.model.mean.item(), source)
            for index, score in pairs
            if self.trained.item_ids[index] not in self.seen[user_id]
        ]
        return sorted(results, key=lambda rec: (-rec.score, rec.item_id))[:top_k]
