from __future__ import annotations

import random

PATHS = ["파멸", "수렵", "지식", "화합", "공허", "보존", "풍요", "기억", "환락"]
ATTRIBUTES = ["물리", "화염", "얼음", "번개", "바람", "양자", "허수"]

PATH_TEXTS = {
    "파멸": "오늘은 무언가를 밀어붙이는 힘이 강한 날이야. 다만 너무 세게 나아가면 주변이 놀랄지도 몰라.",
    "수렵": "목표가 또렷하게 보이는 날이야. 하나를 정했다면 빠르게 움직여도 좋아.",
    "지식": "생각이 넓게 퍼지는 날이야. 평소에 지나쳤던 정보가 새롭게 보일 수 있어.",
    "화합": "누군가와 함께할 때 흐름이 좋아지는 날이야. 작은 대화가 의외의 길을 열어줄 수 있어.",
    "공허": "조금 조용하고 가라앉은 날일 수 있어. 무리해서 밝아지려고 하지 않아도 돼.",
    "보존": "오늘은 지키는 힘이 강한 날이야. 지금 가진 것을 천천히 정리해봐.",
    "풍요": "회복과 돌봄의 흐름이 가까운 날이야. 너 자신을 챙기는 것도 중요한 일이야.",
    "기억": "잊고 있던 것이 다시 떠오르는 날이야. 오래된 기록 속에서 답을 찾을 수 있어.",
    "환락": "가벼운 즐거움이 필요한 날이야. 작은 웃음이 분위기를 바꿔줄 수 있어.",
}

ATTRIBUTE_TEXTS = {
    "물리": "오늘은 직접 부딪히는 힘이 좋아. 몸을 움직이면 풀리는 일이 있을 거야.",
    "화염": "마음속 열기가 강해지는 날이야. 의욕은 좋지만 말이 너무 뜨거워지지 않게 조심해.",
    "얼음": "차분하게 판단하기 좋은 날이야. 감정보다 상황을 먼저 보면 실수를 줄일 수 있어.",
    "번개": "갑작스러운 변화가 찾아올 수 있어. 빠르게 반응하면 오히려 기회가 될 거야.",
    "바람": "흐름을 바꾸기 좋은 날이야. 막혀 있던 일이 있다면 다른 방향에서 접근해봐.",
    "양자": "가능성이 여러 갈래로 펼쳐지는 날이야. 정답이 하나뿐이라고 생각하지 않아도 돼.",
    "허수": "보이지 않던 의미가 천천히 드러나는 날이야. 당장 이해되지 않아도 조금 기다려봐.",
}

DROMAS_LINES = [
    "우웅... 오늘도 너무 무리하지 마.",
    "웅. 좋은 흐름이 가까이 있어.",
    "우우웅... 쉬는 것도 임무야.",
    "우웅! 오늘의 기록은 반짝이고 있어.",
    "웅... 드로마스는 개척자를 응원해.",
    "우웅... 조금 느려도 괜찮아. 길은 계속 이어져 있어.",
]

EXPLORE_RESULTS = [
    "{name}이 반짝이는 먼지를 잔뜩 묻히고 돌아왔어.",
    "{name}이 이상한 돌멩이를 물고 왔어. 쓸모는… 아직 모르겠어.",
    "{name}이 길을 잃을 뻔했지만, 씩씩하게 돌아왔어.",
    "{name}이 별빛 같은 흔적을 발견했어.",
    "{name}은 아무것도 못 찾았지만, 아주 뿌듯해 보여.",
]

def required_exp(level: int) -> int:
    return 100 + (level - 1) * 45

def add_exp(dromas: dict, amount: int) -> tuple[bool, int, int]:
    old_level = int(dromas.get("level", 1))
    dromas["exp"] = int(dromas.get("exp", 0)) + amount
    while dromas["exp"] >= required_exp(int(dromas.get("level", 1))):
        dromas["exp"] -= required_exp(int(dromas.get("level", 1)))
        dromas["level"] = int(dromas.get("level", 1)) + 1
    return int(dromas.get("level", 1)) > old_level, old_level, int(dromas.get("level", 1))

def clamp(value: int, min_value: int = 0, max_value: int = 100) -> int:
    return max(min_value, min(max_value, value))

def roll_fortune() -> dict:
    path = random.choice(PATHS)
    attribute = random.choice(ATTRIBUTES)
    luck = random.randint(1, 100)
    return {
        "path": path,
        "attribute": attribute,
        "luck": luck,
        "path_text": PATH_TEXTS[path],
        "attribute_text": ATTRIBUTE_TEXTS[attribute],
        "line": random.choice(DROMAS_LINES),
    }
