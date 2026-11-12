# recsys-from-scratch

[日本語](README.ja.md) · [English](README.md) · [한국어](README.ko.md)

Python 3.12ベースで最初から実装する推奨システム学習プロジェクトです。

フェーズ1の目標は、小さなCSVデータだけで次の推奨方法を直接実装することです。

- 人気ベースのおすすめ
- User-Item Matrixの生成
- cosine similarity ベースの user-based collaborative filtering

過度のフレームワークなしでコアロジックを直接実装して、推奨システムの基本構造を理解しやすくしました。

## フォルダ構造

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

## インストール

```bash
cd recsys-from-scratch
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

完全な拡張手順はPython 3.12で検証されます。既存のPython 3.9環境の代わりに3.12仮想環境を使用してください。
現在提供されているローカル環境では、`source .venv312/bin/activate`ですぐに開始できます。

## 実行

### ユーザー画面

サーバー実行後に[NEXT](http://127.0.0.1:8000/)に接続すると、コンテンツ推奨画面が開きます。
`/docs`は開発者向けのAPIドキュメントであり、一般ユーザーは`/`を使用しています。

```bash
source .venv312/bin/activate
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

コンテンツをタップして評価を残すと、個人の紹介が更新されます。蒸し、検索、種類/ジャンルフィルター、
評価/年の並べ替え、保存リスト、およびマイ評価の検索をサポートします。私の評価と保存リストはブラウザの
localStorageに保存され、他のデバイスと同期されません。個人評価はおすすめリクエストのみ
使用され、サーバーのソースデータには保存されません。新しい個人的な好みに即座に反映可能
コラボレーションフィルタリングとジャンル/種類の好みを組み合わせます。既存の学習モデル/ APIはそのまま維持します。

現在のコースは学習用の仮想サンプルです。受講申込や決済機能はありません。
インターネットサービスとして公開するには、Python / PyTorchを実行するサーバーの展開とアカウント固有のストレージが必要です。
静的ページのみをホストするとローカルの推奨サーバーに接続できないため、このプロジェクトはFastAPI
画面とAPIを一緒に提供します。

### 拡張コレクション

- コンテンツ308：映画60、シリーズ60、ドキュメンタリー60、書籍60、コース68。
- ジャンル6個：SF・テク、ミステリー、ドラマ、自然、旅行、芸術。
- 仮想ユーザー600人、評価24,000個。乱数シード42で再現可能です。
- `data/catalog.json`：タイトル、説明、種類、ジャンル、年、長さ、画像参照。
- `data/discovery_ratings.csv`: ユーザー別好みのジャンル/種類が反映された合成評価。
- `python -m src.generate_catalog`で拡張データを再生成します。

ホームは代表コンテンツ、横推薦リスト、サンプル評価TOP 10、好きな作品などのジャンル、
種類別の推薦で構成されます。フルナビゲーションでは、24個ずつさらに表示できます。
既存の101～108番講座とブラウザの保存キーを維持し、前の評価と蒸しリストを続けます。

個人推奨スコアは、評価数を補正した平均評価+ジャンル優先+種類優先+近隣評価です。
星点は3点を中立に中心化するので、1～2点は否定好みで反映されます。
ジャンル/種類スコアには少ない評価数の補正を適用し、近隣類似度は共通評価数として
補正します。既に評価したコンテンツは除外します。新規ユーザーは校正された人気スコアを使用します。
画面の星はサンプル平均であり、個人の予測スコアや推奨確率ではありません。

Netflixに似たナビゲーション体験を実装したトレーニングモデルであり、実際のNetflixアルゴリズムの複製ではありません。
拡張画面は`src/discovery.py`を使用します。オリジナル8講座のMF/Two-Tower/FAISSトレーニング データとチェックポイントは、トレーニング比較実験のために別々に保管されます。
合成評価に基づく推奨事項は、実際のユーザー満足度を保証するものではありません。

### CLI

ZZプロテクト3ZZ

予想される出力の例:

ZZプロテクト4ZZ

別のユーザーとして実行することもできます。

ZZプロテクト5ZZ

データパスを変更したい場合:

ZZプロテクト6ZZ

## テスト

ZZプロテクト7ZZ

## アルゴリズムの説明

### 1. 人気に基づく推奨事項

各項目の平均評価とレビュー数を計算します。デフォルトの並べ替え基準は次のとおりです。

1. 平均評価が高い商品
2. 評価数の多い商品
3. item_id が小さいアイテム

特定のユーザーに推奨する場合は、すでに評価されているアイテムを除外します。

### 2. ユーザーとアイテムのマトリックス

次のように、評価ログをネストされた辞書に変換します。

ZZプロテクト8ZZ

これは、典型的なユーザー項目マトリックスのスパース表現です。データが大きくなったときにすべて 0 を保存する必要がないため、これはレコメンダー システムでよく使用される式です。

### 3. コサイン類似度

2 人のユーザーの評価ベクトルがどの程度似ているかを計算します。

ZZプロテクト9ZZ

共通して評価される項目が多く、評価の方向性が類似している場合、類似性は高くなります。

### 4. ユーザーベースの協調フィルタリング

推奨ユーザーがまだ評価していないアイテムについては、類似ユーザーの評価の加重平均がとられます。

ZZプロテクト10ZZ

現在の実装では、正の類似性を持つ近傍のみを使用します。類似度が同じ近傍は、ユーザー ID の降順にソートされます。協調フィルタリングの結果が不十分な場合は、人気に基づいた推奨事項がギャップを埋めます。

## ステップ 2 ～ 5: 学習から API まで

行列分解、Two-Tower、FAISS、および FastAPI が実装されています。
追加ファイルは、`src/models.py`、`training.py`、`train.py`、`retrieval.py`、`api.py`、
新しいテストは `tests/test_models.py`、`tests/test_api.py` にあります。

### 学んで保存する

ZZプロテクト11ZZ

モデルの重み、ID マッピング、学習スコア、
紛失履歴を保存します。ランダムなユーザー/アイテム ID も連続したインデックスにマッピングされます。
トレーニングは CPU 上で実行され、未観測のスコアは 0 ポイントで埋められません。
空のデータ、無限/NaN、および重複するユーザー項目評価は、トレーニング前に拒否されます。
データが変更された場合は、API を再トレーニングして再起動します。

```bash
python -m src.train --algorithm mf --dimension 32 --learning-rate 0.01 --epochs 300
python -m src.main --user-id 1 --top-k 3 --algorithm popular
python -m src.main --user-id 1 --top-k 3 --algorithm cf
python -m src.main --user-id 1 --top-k 3 --algorithm mf
python -m src.main --user-id 1 --top-k 3 --algorithm two-tower
python -m src.main --user-id 1 --top-k 3 --algorithm faiss
```

`--algorithm` のデフォルトは従来の `cf` です。 `--model-dir`でモデルフォルダーを変更できます。
チェックポイントと入力CSVが異なる場合は再トレーニングが必要です。モデルのロード中
トレーニングを再実行しないでください。

### 行列の因数分解

ZZプロテクト13ZZ

PyTorch Embedding と Adam を使用し、観測された評価の損失ループと学習ループを直接実装します。
重みの減衰は `1e-4`、基底ベクトルのサイズは 16 です。出力スコアは未補正の予測値であるため、
値の範囲は 1 ～ 5 であり、確率ではありません。潜在ベクトルの各軸に固定された意味はありません。

### ツータワー

各ユーザーおよびアイテムに `Embedding -> Linear -> ReLU -> Linear` を適用します。
全体の平均を 2 つのベクトルの内積に加算し、MF と同じ観測スコア MSE で学習します。
項目ベクトルはユーザーとは独立して事前に計算し、検索インデックスにリンクできます。現在はIDのみを使用する評価回帰型Two-Towerです。テキスト/カテゴリの特徴
音声サンプリング、対照学習はまだ含まれていません。

### FAISS

`--algorithm faiss`は学習したTwo-Towerのアイテムベクトルを`IndexFlatIP`に入れて
内的検索します。ベクトルを正規化しないので、コサインではなく学習スコアなどの内積です。
全体の平均はすべての候補に同じであるため、検索ランキングには影響しません。
すでに評価されているアイテムを除いて、タイはアイテムIDでソートされます。

現在、インデックスは正確な検索であり、近似検索（ANN）ではありません。小さなサンプルでタイと除外処理
検証するために候補全体を照会します。大規模サービスに拡張する場合は、候補数の制限、
フィルタリング後、追加の照会、IVF / HNSWなどを確認する必要があります。インデックスはサーバーの起動時に再生成されます。

### FastAPIの実行

```bash
python -m src.train --algorithm all
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

- インタラクティブAPIドキュメント：http://127.0.0.1:8000/docs
- 状態: `GET /health`
- おすすめ：`GET /recommendations?user_id=1&top_k=3&algorithm=faiss`

```bash
curl 'http://127.0.0.1:8000/recommendations?user_id=1&top_k=3&algorithm=faiss'
```

応答には`user_id`、`algorithm`、`recommendations`が含まれます。各おすすめに
`item_id`、`title`、`score`、`source`があります。 `top_k`は1〜100であり、
無効なオプションは422を返します。初めて見るユーザーは人気のおすすめを返し、
推奨する未評価アイテムがない場合は、空のリストを返します。
学習ファイルがない場合、そのモデル要求は503、既存の人気/ CF推薦は正常に動作します。
モデルとインデックスはサーバー起動時に一度だけ準備され、要求ごとに学習しません。
`RECSYS_DATA_DIR`、`RECSYS_MODEL_DIR`環境変数にパスを変更できます。

### 検証範囲と次の課題

```bash
python -m pytest -q
```

既存のCFテストに加えて、学習損失の減少、チェックポイントの復元、外部IDマッピング、FAISSとの直接内積
一致、既に評価された項目を除外、新規ユーザー、入力エラー、CLI、API を検証します。
サンプル全体で学習したMSEは学習動作を確認するためのものであり、推奨品質や一般化パフォーマンスの証拠ではありません。
実際のポートフォリオ評価には、時間ベースのtrain/validation/test分離、RMSEとRecall@K/NDCG@K、
人気の推奨コントラスト比較を追加します。その後、Two-Towerに特徴と対照学習を追加し、
FAISS近似検索の精度/遅延時間比較、API負荷テストの順に拡張できます。

公式参考資料：[PyTorch Adam]（https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html）、
[FAISSインデックス](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)、
[FastAPIテスト]（https://fastapi.tiangolo.com/tutorial/testing/）。

### ローカル検証履歴

Python 3.12.14 / macOS arm64で31のテストが合格しました。
200エポック学習MSEはMF薬`0.399352 -> 0.000000`、Two-Tower薬
`0.408970 -> 0.000001`でした。丸められた学習損失であり、検証セットのスコアではありません。
依存ライブラリで5つのデプレケーション警告が発生しましたが、失敗したテストはありません。
CLIの5つの推奨方法と実際のHTTPの`/health`、`/recommendations`、`/docs`の応答を確認しました。
