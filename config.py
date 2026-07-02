# -*- coding: utf-8 -*-
"""데일리 마켓 리포트 설정"""

# 차트로 그릴 지수 (KRX 지수 티커)
INDICES = {
    "KOSPI": "1001",
    "KOSDAQ": "2001",
}

# 섹터별 ETF 그룹 (블로그 레이아웃과 동일한 묶음)
# 이름은 KRX 상장명과 비슷하게만 적으면 됨 — 실행 시 자동으로 정확한 티커를 찾음
ETF_GROUPS = [
    ("시장/반도체", [
        "KODEX 코스닥150",
        "KODEX 반도체",
        "KODEX AI반도체핵심장비",
    ]),
    ("에너지", [
        "RISE 2차전지액티브",
        "PLUS 태양광&ESS",
        "TIGER Fn신재생에너지",
        "HANARO 원자력iSelect",
    ]),
    ("전력/조선/방산/우주", [
        "KODEX AI전력핵심설비",
        "SOL 조선TOP3플러스",
        "PLUS K방산",
        "PLUS 우주항공&UAM",
    ]),
    ("자동차/로봇/바이오/의료기기", [
        "KODEX 자동차",
        "KODEX K-로봇액티브",
        "TIMEFOLIO K바이오액티브",
        "SOL 의료기기소부장",
    ]),
    ("소재/건설/인터넷", [
        "TIGER 200 에너지화학",
        "KODEX 철강",
        "KODEX 건설",
        "TIGER 인터넷TOP10",
    ]),
    ("K컬처/소비재", [
        "ACE KPOP포커스",
        "TIGER 화장품",
        "HANARO Fn K-푸드",
        "TIGER K게임",
    ]),
    ("여행/콘텐츠/지주", [
        "TIGER 여행레저",
        "KODEX 웹툰&드라마",
        "TIGER 지주회사",
    ]),
    ("금융", [
        "KODEX 증권",
        "KODEX 은행",
        "KODEX 보험",
    ]),
]

# 차트 설정
CHART_LOOKBACK_DAYS = 180        # 차트에 표시할 기간 (캘린더 기준)
MA_WINDOWS = (5, 20, 60)         # 이동평균선
CHART_DIR = "charts"             # 차트 저장 폴더 (레포에 커밋됨)

# 정배열 판정: 종가 > MA5 > MA20 > MA60 이면 "정배열"
# MA간 간격이 ±1% 이내로 얽혀 있으면 "중립/걸침"

# 리포트 설정
TOP_VALUE_COUNT = 10             # 거래대금 상위 종목 수 (시장별)
NEW_HIGH_MAX = 20                # 52주 신고가 표시 최대 종목 수 (시장별)

# 텔레그램 메시지 최대 길이 (텔레그램 제한 4096)
TG_MAX_LEN = 4000
