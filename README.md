# recsys-from-scratch

[日本語](README.ja.md) · [English](README.md) · [한국어](README.ko.md)

This is a recommender system learning project implemented from scratch based on Python 3.12.

The goal of phase 1 is to directly implement the following recommendation method with only small CSV data.

- Popularity-based recommendations
- Creation of User-Item Matrix
- User-based collaborative filtering based on cosine similarity

We made the basic structure of the recommendation system easy to understand by directly implementing the core logic without an excessive framework.

## Folder structure

```text
recsys-from-scratch/
  data/
    items.csv
    ratings.csv
  src/
    __init__.py
    data_loader.py
    main.py
    metrics.py
    recommender.py
    models.py
    training.py
    train.py
    retrieval.py
    api.py
  tests/
    test_recommender.py
    test_models.py
    test_api.py
  artifacts/              # 학습 시 생성, Git 제외
  requirements.txt
  README.md
```

## Installation

```bash
cd recsys-from-scratch
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The entire extension step is verified in Python 3.12. Use the 3.12 virtual environment instead of the existing Python 3.9 environment.
In the local environment currently provided, you can get started right away with `source .venv312/bin/activate`.

## run

### User screen

After running the server and connecting to [NEXT](http://127.0.0.1:8000/), a content recommendation screen will open.
`/docs` is an API document for developers, while general users use `/`.

```bash
source .venv312/bin/activate
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

If you click on the content and leave a rating, your personal recommendation will be updated. Save, search, type/genre filter,
Supports rating/year sorting, saved lists, and viewing my ratings. My ratings and saved lists can be found in your browser.
It is stored in localStorage and does not sync with other devices. Personal ratings are only available for recommendation requests
It is used and not stored in the original data on the server. New personal preferences can be immediately reflected
Combines collaborative filtering and genre/type preferences. Existing learning models/APIs remain intact.

The current course is a virtual sample for learning purposes. There is no course registration or payment function.
To publish as an Internet service, you need to deploy a server to run Python/PyTorch and a repository for each account.
This project supports FastAPI because hosting only static pages will not allow you to connect to local referral servers.
Provides both screen and API.

### Extended Collection

- 308 contents: 60 movies, 60 series, 60 documentaries, 60 books, 68 courses.
- 6 genres: SF/Tech, Mystery, Drama, Nature, Travel, Art.
- 600 virtual users, 24,000 ratings. It can be reproduced with a random number seed of 42.
- `data/catalog.json`: Title, description, type, genre, year, length, image reference.
- `data/discovery_ratings.csv`: Composite rating reflecting each user’s preferred genre/type.
- Regenerate extended data with `python -m src.generate_catalog`.

Home contains genres such as representative content, horizontal recommendation list, top 10 sample ratings, and favorite works,
It consists of recommendations by type. You can see 24 more in full navigation.
The existing courses 101 to 108 and browser save keys will be maintained to maintain previous ratings and wish lists.

The personal recommendation score is the average rating adjusted for the number of reviews + genre preference + type preference + neighborhood rating.
The star rating is centered around 3 points as neutral, so 1 to 2 points are reflected as negative taste.
Correction for the small number of evaluations is applied to the genre/type score, and neighbor similarity is calculated by the number of common evaluations.
Correct. Excludes content that has already been rated. New users use a calibrated popularity score.
The star ratings on screen are sample averages and are not individual predicted scores or odds of being recommended.

This is an educational model that implements a Netflix-like browsing experience and is not a replication of the actual Netflix algorithm.
The extended screen uses `src/discovery.py`. MF/Two-Tower/FAISS in the original 8 coursesTraining data and checkpoints are kept separate for training comparison experiments.
Recommendations that operate on synthetic ratings do not guarantee actual user satisfaction.

### CLI

```bash
python -m src.main --user-id 1 --top-k 3
```

Example expected output:

```text
Recommendations for user 1

rank  item_id  title                         score   source
1     105      FastAPI for ML APIs           4.739   collaborative
2     107      Practical PyTorch             4.505   collaborative
3     104      Deep Learning Foundations     4.495   collaborative
```

You can also run it as a different user.

```bash
python -m src.main --user-id 4 --top-k 5
```

If you want to change the data path:

```bash
python -m src.main \
  --ratings-path data/ratings.csv \
  --items-path data/items.csv \
  --user-id 1 \
  --top-k 3
```

## test

```bash
pytest
```

## Algorithm description

### 1. Popularity-based recommendations

Calculate the average rating and number of reviews for each item. The default sorting criteria are:

1. Items with a high average rating
2. Items with a high number of ratings
3. Items with small item_id

When recommending to a specific user, exclude items that have already been rated.

### 2. User-Item Matrix

Convert the rating log into a nested dictionary like this:

```python
{
    1: {101: 5.0, 102: 4.0},
    2: {101: 4.0, 103: 5.0},
}
```

This is a sparse representation of a typical User-Item Matrix. This is an expression often used in recommender systems because there is no need to store all 0s when the data grows.

### 3. Cosine Similarity

Calculate how similar the rating vectors of two users are.

```text
similarity(u, v) = dot(u, v) / (||u|| * ||v||)
```

If there are many items evaluated in common and the rating directions are similar, the similarity increases.

### 4. User-Based Collaborative Filtering

For items that the recommended user has not yet rated, we take a weighted average of the ratings of similar users.

```text
predicted_score(user, item)
  = sum(similarity(user, neighbor) * neighbor_rating)
    / sum(similarity(user, neighbor))
```

The current implementation only uses neighbors with positive similarity. Neighbors with the same similarity are sorted in descending order of user ID. If collaborative filtering results are insufficient, popularity-based recommendations fill in the gaps.

## Steps 2 to 5: From learning to API

Matrix Factorization, Two-Tower, FAISS, and FastAPI are implemented.
Additional files are `src/models.py`, `training.py`, `train.py`, `retrieval.py`, `api.py`,
The new tests are in `tests/test_models.py`, `tests/test_api.py`.

### Learn and Save

```bash
python -m src.train --algorithm all --epochs 200 --seed 42
```

Model weights, ID mapping, learning scores,
Save your loss history. Random user/item IDs are also mapped to consecutive indices.
Training is performed on the CPU, and unobserved scores are not filled with 0 points.
Empty data, infinity/NaN, and duplicate user-item ratings are rejected before training.
If the data changes, retrain and restart the API.

```bash
python -m src.train --algorithm mf --dimension 32 --learning-rate 0.01 --epochs 300
python -m src.main --user-id 1 --top-k 3 --algorithm popular
python -m src.main --user-id 1 --top-k 3 --algorithm cf
python -m src.main --user-id 1 --top-k 3 --algorithm mf
python -m src.main --user-id 1 --top-k 3 --algorithm two-tower
python -m src.main --user-id 1 --top-k 3 --algorithm faiss
```

`--algorithm` defaults to the legacy `cf`. You can change the model folder with `--model-dir`.
If the checkpoint and input CSV are different, retraining is required. In the process of loading the model
Do not re-run training.

### Matrix Factorization

```text
predicted_rating(u, i) = global_mean + dot(user_embedding[u], item_embedding[i])
loss = MSE(observed_ratings, predicted_ratings)
```

We use PyTorch Embedding and Adam, and directly implement the loss and learning loops for the observed ratings.
Weight attenuation is `1e-4`, base vector size is 16. Since the output score is the uncorrected predicted value,
It can range from 1 to 5 and is not a probability. There is no fixed meaning for each axis of the latent vector.

### Two-Tower

Apply `Embedding -> Linear -> ReLU -> Linear` to each user and item.
Add the overall mean to the dot product of the two vectors and learn with the same observation score MSE as MF.
Item vectors can be pre-computed independently of the user and linked to the search index.Currently, it is a rating regression type Two-Tower that only uses ID. Text/category features or
It does not yet include voice sampling or contrastive learning.

### FAISS

`--algorithm faiss` puts the learned Two-Tower item vector into `IndexFlatIP`.
Dot product search. We don't normalize the vector, so it's a dot product equal to the training score, not cosine.
The overall average is the same for all candidates, so it doesn't affect search rankings.
Tied scores are sorted by item ID, excluding items that have already been rated.

The current index is exact search, not approximate search (ANN). Handling ties and exclusions in small samples
View all candidates for verification. When scaling to large-scale services, limit the number of candidates;
After filtering, you will need to review additional inquiries, IVF/HNSW, etc. Indexes are regenerated when the server starts.

### FastAPI execution

```bash
python -m src.train --algorithm all
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

- Interactive API Documentation: http://127.0.0.1:8000/docs
- Status: `GET /health`
- Recommended: `GET /recommendations?user_id=1&top_k=3&algorithm=faiss`

```bash
curl 'http://127.0.0.1:8000/recommendations?user_id=1&top_k=3&algorithm=faiss'
```

Responses include `user_id`, `algorithm`, and `recommendations`. In each recommendation
There are `item_id`, `title`, `score`, and `source`. `top_k` is 1 to 100,
An invalid option returns 422. First-time users will return popular recommendations,
If there are no unrated items to recommend, it returns an empty list.
If there is no training file, the model request will receive 503, and existing popularity/CF recommendations will operate normally.
Models and indices are prepared once at server startup and are not trained per request.
You can change the path with the `RECSYS_DATA_DIR` and `RECSYS_MODEL_DIR` environment variables.

### Verification scope and next tasks

```bash
python -m pytest -q
```

In addition to traditional CF tests, learning loss reduction, checkpoint restoration, external ID mapping, FAISS and direct dot product
Verify matches, exclude already rated items, new users, input errors, CLI and API.
MSEs trained across samples are intended to confirm learning behavior and are not evidence of recommendation quality or generalization performance.
Actual portfolio evaluation includes time-based train/validation/test separation, RMSE and Recall@K/NDCG@K,
Add comparisons to popular recommendations. Afterwards, feature and contrast learning were added to Two-Tower,
It can be expanded in that order: accuracy/latency comparison of FAISS approximate search, and API load testing.

Official references: [PyTorch Adam](https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html),
[FAISS INDEX](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes),
[FastAPI Test](https://fastapi.tiangolo.com/tutorial/testing/).

### Local verification history

31 tests passed on Python 3.12.14 / macOS arm64.
200 epoch learning MSE is about MF `0.399352 -> 0.000000`, Two-Tower about
It was `0.408970 -> 0.000001`. This is the rounded training loss, not the validation set score.
There were 5 deprecation warnings in dependent libraries, but no tests failed.
We checked the five recommended methods of CLI and the actual HTTP responses `/health`, `/recommendations`, and `/docs`.
