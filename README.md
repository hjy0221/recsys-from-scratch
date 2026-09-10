# recsys-from-scratch

Python 3.12 기준으로 처음부터 구현하는 추천시스템 학습 프로젝트입니다.

1단계 목표는 작은 CSV 데이터만으로 다음 추천 방식을 직접 구현하는 것입니다.

- 인기 기반 추천
- User-Item Matrix 생성
- cosine similarity 기반 user-based collaborative filtering

과도한 프레임워크 없이 핵심 로직을 직접 구현해서 추천시스템의 기본 구조를 이해하기 쉽게 만들었습니다.

## 폴더 구조

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

## 설치

```bash
cd recsys-from-scratch
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

전체 확장 단계는 Python 3.12에서 검증합니다. 기존 Python 3.9 환경 대신 3.12 가상환경을 사용하세요.
현재 제공된 로컬 환경에서는 `source .venv312/bin/activate`로 바로 시작할 수 있습니다.

## 실행

### 사용자 화면

서버 실행 후 [NEXT](http://127.0.0.1:8000/)에 접속하면 콘텐츠 추천 화면이 열립니다.
`/docs`는 개발자용 API 문서이며, 일반 사용자는 `/`를 사용합니다.

```bash
source .venv312/bin/activate
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

콘텐츠를 눌러 평점을 남기면 개인 추천이 갱신됩니다. 찜하기, 검색, 종류/장르 필터,
평점/연도 정렬, 저장 목록과 내 평점 조회를 지원합니다. 내 평점과 저장 목록은 브라우저의
localStorage에 보관되며, 다른 기기와 동기화되지 않습니다. 개인 평점은 추천 요청에만
사용되고 서버의 원본 데이터에는 저장되지 않습니다. 새 개인 취향에는 즉시 반영 가능한
협업 필터링과 장르/종류 취향을 결합합니다. 기존 학습 모델/API는 그대로 유지합니다.

현재 강좌는 학습용 가상 샘플입니다. 수강 신청이나 결제 기능은 없습니다.
인터넷 서비스로 공개하려면 Python/PyTorch를 실행할 서버 배포와 계정별 저장소가 필요합니다.
정적 페이지만 호스팅하면 로컬 추천 서버에 연결할 수 없으므로 이 프로젝트는 FastAPI가
화면과 API를 함께 제공합니다.

### 확장 컬렉션

- 콘텐츠 308개: 영화 60, 시리즈 60, 다큐 60, 도서 60, 강좌 68개.
- 장르 6개: SF·테크, 미스터리, 드라마, 자연, 여행, 예술.
- 가상 사용자 600명, 평점 24,000개. 난수 seed 42로 재현 가능합니다.
- `data/catalog.json`: 제목, 설명, 종류, 장르, 연도, 길이, 이미지 참조.
- `data/discovery_ratings.csv`: 사용자별 선호 장르/종류가 반영된 합성 평점.
- `python -m src.generate_catalog`로 확장 데이터를 다시 생성합니다.

홈은 대표 콘텐츠, 가로 추천 목록, 샘플 평점 TOP 10, 좋아한 작품과 같은 장르,
종류별 추천으로 구성됩니다. 전체 탐색에서는 24개씩 더 볼 수 있습니다.
기존 101~108번 강좌와 브라우저 저장 키를 유지해 이전 평점과 찜 목록을 이어갑니다.

개인 추천 점수는 평가 수를 보정한 평균 평점 + 장르 선호 + 종류 선호 + 이웃 평점입니다.
별점은 3점을 중립으로 중심화하므로 1~2점은 부정 취향으로 반영됩니다.
장르/종류 점수에는 적은 평가 수에 대한 보정을 적용하고, 이웃 유사도는 공통 평가 수로
보정합니다. 이미 평가한 콘텐츠는 제외합니다. 신규 사용자는 보정된 인기 점수를 사용합니다.
화면의 별점은 샘플 평균이며 개인 예측 점수나 추천 확률이 아닙니다.

넷플릭스와 유사한 탐색 경험을 구현한 교육용 모델이며 실제 넷플릭스 알고리즘의 복제는 아닙니다.
확장 화면은 `src/discovery.py`를 사용합니다. 원래 8개 강좌의 MF/Two-Tower/FAISS
학습 데이터와 체크포인트는 교육용 비교 실험을 위해 별도로 유지됩니다.
합성 평점에서 작동하는 추천이 실제 이용자의 만족도를 보장하지는 않습니다.

### CLI

```bash
python -m src.main --user-id 1 --top-k 3
```

예상 출력 예시:

```text
Recommendations for user 1

rank  item_id  title                         score   source
1     105      FastAPI for ML APIs           4.739   collaborative
2     107      Practical PyTorch             4.505   collaborative
3     104      Deep Learning Foundations     4.495   collaborative
```

다른 사용자로 실행할 수도 있습니다.

```bash
python -m src.main --user-id 4 --top-k 5
```

데이터 경로를 바꾸고 싶다면:

```bash
python -m src.main \
  --ratings-path data/ratings.csv \
  --items-path data/items.csv \
  --user-id 1 \
  --top-k 3
```

## 테스트

```bash
pytest
```

## 알고리즘 설명

### 1. 인기 기반 추천

아이템별 평균 평점과 평가 수를 계산합니다. 기본 정렬 기준은 다음과 같습니다.

1. 평균 평점이 높은 아이템
2. 평가 수가 많은 아이템
3. item_id가 작은 아이템

특정 사용자에게 추천할 때는 이미 평가한 아이템을 제외합니다.

### 2. User-Item Matrix

평점 로그를 다음과 같은 중첩 딕셔너리 형태로 바꿉니다.

```python
{
    1: {101: 5.0, 102: 4.0},
    2: {101: 4.0, 103: 5.0},
}
```

이는 일반적인 User-Item Matrix의 sparse representation입니다. 데이터가 커졌을 때 0을 전부 저장하지 않아도 되기 때문에 추천시스템에서 자주 쓰는 표현입니다.

### 3. Cosine Similarity

두 사용자의 평점 벡터가 얼마나 비슷한지 계산합니다.

```text
similarity(u, v) = dot(u, v) / (||u|| * ||v||)
```

공통으로 평가한 아이템이 많고 평점 방향이 비슷하면 유사도가 높아집니다.

### 4. User-Based Collaborative Filtering

추천 대상 사용자가 아직 평가하지 않은 아이템에 대해, 비슷한 사용자의 평점을 가중 평균합니다.

```text
predicted_score(user, item)
  = sum(similarity(user, neighbor) * neighbor_rating)
    / sum(similarity(user, neighbor))
```

현재 구현은 양수 유사도를 가진 이웃만 사용합니다. 유사도가 같은 이웃은 사용자 ID가 작은 순서로 정렬합니다. collaborative filtering 결과가 부족하면 인기 기반 추천으로 부족한 개수를 채웁니다.

## 2~5단계: 학습부터 API까지

Matrix Factorization, Two-Tower, FAISS, FastAPI가 구현되어 있습니다.
추가 파일은 `src/models.py`, `training.py`, `train.py`, `retrieval.py`, `api.py`이며,
새 테스트는 `tests/test_models.py`, `tests/test_api.py`에 있습니다.

### 학습과 저장

```bash
python -m src.train --algorithm all --epochs 200 --seed 42
```

`artifacts/mf.pt`와 `artifacts/two-tower.pt`에 모델 가중치, ID 매핑, 학습 평점,
손실 기록을 저장합니다. 임의의 사용자/아이템 ID도 연속 인덱스로 매핑됩니다.
학습은 CPU에서 실행하며, 미관측 평점을 0점으로 채워 학습하지 않습니다.
빈 데이터, 무한대/NaN, 중복 사용자-아이템 평점은 학습 전에 거부합니다.
데이터가 바뀌면 다시 학습하고 API를 재시작하세요.

```bash
python -m src.train --algorithm mf --dimension 32 --learning-rate 0.01 --epochs 300
python -m src.main --user-id 1 --top-k 3 --algorithm popular
python -m src.main --user-id 1 --top-k 3 --algorithm cf
python -m src.main --user-id 1 --top-k 3 --algorithm mf
python -m src.main --user-id 1 --top-k 3 --algorithm two-tower
python -m src.main --user-id 1 --top-k 3 --algorithm faiss
```

`--algorithm` 기본값은 기존 `cf`입니다. `--model-dir`로 모델 폴더를 바꿀 수 있습니다.
체크포인트와 입력 CSV가 다르면 재학습을 요구합니다. 모델을 불러오는 과정에서
학습을 다시 실행하지 않습니다.

### Matrix Factorization

```text
predicted_rating(u, i) = global_mean + dot(user_embedding[u], item_embedding[i])
loss = MSE(observed_ratings, predicted_ratings)
```

PyTorch Embedding과 Adam을 사용하고, 관측된 평점에 대한 손실과 학습 반복문은 직접 구현합니다.
가중치 감쇠는 `1e-4`, 기본 벡터 크기는 16입니다. 출력 점수는 보정하지 않은 예측값이므로
1~5 범위를 벗어날 수 있고 확률이 아닙니다. 잠재 벡터의 각 축에 고정된 의미는 없습니다.

### Two-Tower

사용자와 아이템 각각에 `Embedding -> Linear -> ReLU -> Linear`를 적용합니다.
두 벡터의 내적에 전체 평균을 더하고, MF와 동일한 관측 평점 MSE로 학습합니다.
아이템 벡터를 사용자와 독립적으로 미리 계산할 수 있어 검색 인덱스와 연결됩니다.
현재는 ID만 사용하는 평점 회귀형 Two-Tower입니다. 텍스트/카테고리 특징이나
음성 샘플링, 대조 학습은 아직 포함하지 않습니다.

### FAISS

`--algorithm faiss`는 학습된 Two-Tower의 아이템 벡터를 `IndexFlatIP`에 넣어
내적 검색합니다. 벡터를 정규화하지 않으므로 cosine이 아닌 학습 점수와 같은 내적입니다.
전체 평균은 모든 후보에 동일하므로 검색 순위에 영향을 주지 않습니다.
이미 평가한 아이템을 제외하고 동점은 아이템 ID로 정렬합니다.

현재 인덱스는 정확 검색이며 근사 검색(ANN)이 아닙니다. 작은 샘플에서 동점과 제외 처리를
검증하기 위해 전체 후보를 조회합니다. 대규모 서비스로 확장할 때는 후보 수 제한,
필터링 후 추가 조회, IVF/HNSW 등을 검토해야 합니다. 인덱스는 서버 시작 때 재생성합니다.

### FastAPI 실행

```bash
python -m src.train --algorithm all
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

- 대화형 API 문서: http://127.0.0.1:8000/docs
- 상태: `GET /health`
- 추천: `GET /recommendations?user_id=1&top_k=3&algorithm=faiss`

```bash
curl 'http://127.0.0.1:8000/recommendations?user_id=1&top_k=3&algorithm=faiss'
```

응답은 `user_id`, `algorithm`, `recommendations`를 포함합니다. 각 추천에는
`item_id`, `title`, `score`, `source`가 있습니다. `top_k`는 1~100이며,
잘못된 옵션은 422를 반환합니다. 처음 보는 사용자는 인기 추천을 반환하고,
추천할 미평가 아이템이 없으면 빈 목록을 반환합니다.
학습 파일이 없으면 해당 모델 요청은 503, 기존 인기/CF 추천은 정상 동작합니다.
모델과 인덱스는 서버 시작 시 한 번만 준비하며 요청마다 학습하지 않습니다.
`RECSYS_DATA_DIR`, `RECSYS_MODEL_DIR` 환경변수로 경로를 변경할 수 있습니다.

### 검증 범위와 다음 과제

```bash
python -m pytest -q
```

기존 CF 테스트 외에 학습 손실 감소, 체크포인트 복원, 외부 ID 매핑, FAISS와 직접 내적의
일치, 이미 평가한 항목 제외, 신규 사용자, 입력 오류, CLI 및 API를 검증합니다.
샘플 전체로 학습한 MSE는 학습 동작 확인용이며 추천 품질이나 일반화 성능의 증거가 아닙니다.
실제 포트폴리오 평가에는 시간 기반 train/validation/test 분리, RMSE와 Recall@K/NDCG@K,
인기 추천 대비 비교를 추가하세요. 이후 Two-Tower에 특징과 대조 학습을 추가하고,
FAISS 근사 검색의 정확도/지연시간 비교, API 부하 테스트 순으로 확장할 수 있습니다.

공식 참고 자료: [PyTorch Adam](https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html),
[FAISS 인덱스](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes),
[FastAPI 테스트](https://fastapi.tiangolo.com/tutorial/testing/).

### 로컬 검증 기록

Python 3.12.14 / macOS arm64에서 테스트 31개가 통과했습니다.
200 epoch 학습 MSE는 MF 약 `0.399352 -> 0.000000`, Two-Tower 약
`0.408970 -> 0.000001`이었습니다. 반올림된 학습 손실이며 검증셋 점수가 아닙니다.
의존 라이브러리에서 deprecation warning 5개가 발생했으나 실패한 테스트는 없습니다.
CLI의 다섯 추천 방식과 실제 HTTP의 `/health`, `/recommendations`, `/docs` 응답을 확인했습니다.
