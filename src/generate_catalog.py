"""Generate fictional catalog and taste-correlated interactions, deterministically."""

import csv
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
GENRES = {
    "SF·테크": ("space", ["마지막 궤도", "기억의 설계자", "푸른 행성의 신호", "내일의 코드", "달의 반대편", "인공의 마음", "두 번째 지구", "빛의 좌표", "미래의 경계", "밤의 알고리즘"]),
    "미스터리": ("city", ["사라진 지도", "새벽 세 시", "침묵의 목격자", "잠긴 방의 편지", "안개 속의 역", "낯선 방문자", "기억하지 못한 밤", "아홉 번째 단서", "검은 우편함", "마지막 기록"]),
    "드라마": ("coast", ["우리가 머문 계절", "조용한 오후", "다시 만나는 날", "여름의 끝에서", "당신의 작은 우주", "집으로 가는 길", "이름 없는 하루", "오래된 약속", "서로의 풍경", "느리게 흐르는 시간"]),
    "자연": ("forest", ["숲이 건네는 말", "초록의 시간", "살아 있는 지구", "바람의 흔적", "깊은 산의 아침", "작은 생명의 세계", "물길을 따라서", "계절의 문턱", "숨 쉬는 대지", "자연의 기억"]),
    "여행": ("mountain", ["낯선 도시의 아침", "지도의 바깥", "길 위의 하루", "느린 여행자의 노트", "북쪽으로 가는 기차", "경계 너머의 풍경", "바다를 만나는 길", "여행의 온도", "산 너머 작은 마을", "돌아오지 않은 엽서"]),
    "예술": ("art", ["색의 기억", "빛을 모으는 사람", "소리의 풍경", "작업실의 오후", "보이지 않는 리듬", "그림 너머의 이야기", "일상의 시선", "빈 무대의 약속", "아름다움의 발견", "한 장의 세계"]),
}
TYPES = ["영화", "시리즈", "다큐", "도서", "강좌"]


def generate():
    rng = random.Random(42)
    records = []
    with (ROOT / "data/items.csv").open(encoding="utf-8") as source:
        for row in csv.DictReader(source):
            records.append(dict(item_id=int(row["item_id"]), title=row["title"], category="강좌",
                                genre="SF·테크", description="코드와 데이터로 배우는 실전 기술의 기초.",
                                image="code", year=2025, duration="8개 챕터", audience="입문", fictional=True))
    for type_index, kind in enumerate(TYPES):
        for genre_index, (genre, (image, titles)) in enumerate(GENRES.items()):
            for number, title in enumerate(titles):
                suffix = {"영화": "", "시리즈": ": 이어지는 이야기", "다큐": ": 그 이면의 세계",
                          "도서": ": 한 권의 기록", "강좌": ": 시선과 표현 배우기"}[kind]
                descriptions = {
                    "영화": f"{title}. 익숙했던 세계에 작은 균열이 생기고, 새로운 선택이 시작된다. {genre}의 감각을 담은 가상의 영화.",
                    "시리즈": f"{title}에서 시작된 이야기가 각자의 삶을 따라 이어진다. 매회 새로운 시선으로 만나는 {genre} 시리즈.",
                    "다큐": f"{genre}의 세계를 가까이 들여다보는 관찰의 여정. {title}에 담긴 질문을 따라가는 가상의 다큐멘터리.",
                    "도서": f"{title}에 대한 생각과 장면을 한 권에 모았다. {genre}에 관심 있는 독자를 위한 가상의 읽을거리.",
                    "강좌": f"{genre}를 소재로 관찰하고 이야기를 구성하는 연습. {title}에서 출발해 나만의 결과물을 만드는 가상의 강좌.",
                }
                records.append(dict(item_id=1000+type_index*60+genre_index*10+number,
                                    title=title+suffix, category=kind, genre=genre, description=descriptions[kind],
                                    image=image, year=2021+rng.randrange(6),
                                    duration={"영화":f"{90+rng.randrange(50)}분", "시리즈":f"{6+rng.randrange(7)}부작",
                                              "다큐":f"{40+rng.randrange(50)}분", "도서":f"{180+rng.randrange(200)}쪽",
                                              "강좌":f"{6+rng.randrange(9)}개 챕터"}[kind],
                                    audience="전체" if genre in ("자연", "여행", "예술") else "12+", fictional=True))
    interactions = []
    for user_id in range(1, 601):
        favorite = list(GENRES)[(user_id-1) % len(GENRES)]
        preferred_type = TYPES[(user_id-1)//len(GENRES) % len(TYPES)]
        chosen = rng.sample(records, 40)
        for record in chosen:
            score = 2.5 + 1.25*(record["genre"] == favorite) + 0.6*(record["category"] == preferred_type) + rng.gauss(0, 0.6)
            interactions.append((user_id, record["item_id"], max(1, min(5, round(score)))))
    (ROOT / "data/catalog.json").write_text(json.dumps(records, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with (ROOT / "data/discovery_ratings.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["user_id", "item_id", "rating"])
        writer.writerows(interactions)
    print(f"Generated {len(records)} items, 600 synthetic users, {len(interactions)} ratings (seed=42)")


if __name__ == "__main__":
    generate()
