# -*- coding: utf-8 -*-
"""리포트 본문 조립 (텔레그램/노션 공용 텍스트)"""
import datetime as dt


def _fmt_flow(v):
    return f"{'매수' if v > 0 else '매도'} {abs(v):,.0f}억"


def build_daily_text(date, alignments, deposits, flows, tops, limit_ups, new_highs):
    d = f"{date[:4]}.{date[4:6]}.{date[6:]}"
    L = [f"📊 데일리 마켓 리포트 — {d}", ""]

    # 1. ETF 배열 판정
    L.append("1️⃣ 섹터 ETF 배열 (차트 이미지 참고)")
    for key in ("정배열", "중립/걸침", "혼조", "역배열"):
        if alignments.get(key):
            L.append(f"  • {key}: {', '.join(alignments[key])}")
    L.append("")

    # 2. 고객예탁금
    L.append("2️⃣ 증시 자금 (금투협 D-1)")
    if deposits:
        L.append(f"  • 고객예탁금 {deposits['고객예탁금']:.0f}조 / 신용잔고 {deposits['신용잔고']:.0f}조")
    else:
        L.append("  • 수집 실패 — 금투협 FreeSIS에서 확인 필요")
    L.append("")

    # 3. 거래대금 상위
    L.append("3️⃣ 거래대금 상위")
    for market in ("KOSPI", "KOSDAQ"):
        L.append(f"  [{market}]")
        if tops.get(market):
            for name, value, chg in tops[market]:
                L.append(f"    {name} {value:,.0f}억 ({chg:+.1f}%)")
        else:
            L.append("    수집 실패")
    lu_lines = []
    for market in ("KOSPI", "KOSDAQ"):
        for name, chg in (limit_ups.get(market) or []):
            lu_lines.append(name)
    L.append(f"  상한가) {', '.join(lu_lines) if lu_lines else '없음'}")
    L.append("")

    # 4. 투자자별 매매동향
    L.append("4️⃣ 투자자별 매매동향")
    for market in ("KOSPI", "KOSDAQ"):
        f = flows.get(market)
        if f:
            L.append(f"  {market}: 개인 {_fmt_flow(f['개인'])} / 외인 {_fmt_flow(f['외국인'])} / 기관 {_fmt_flow(f['기관'])}")
        else:
            L.append(f"  {market}: 수집 실패")
    L.append("")

    # 5. 52주 신고가
    L.append("5️⃣ 52주 신고가")
    for market in ("KOSPI", "KOSDAQ"):
        names = new_highs.get(market)
        L.append(f"  [{market}] {', '.join(names) if names else '수집 실패/없음'}")
    L.append("")
    L.append("6️⃣ EVENT & ISSUE")
    L.append("  (수동 작성 영역)")
    return "\n".join(L)


def build_periodic_text(mode: str, date: str, perf: list):
    """주간/월간: ETF 기간 수익률 랭킹.
    perf = [(이름, 수익률%), ...] 정렬 전"""
    label = "주간" if mode == "weekly" else "월간"
    d = f"{date[:4]}.{date[4:6]}.{date[6:]}"
    perf = sorted(perf, key=lambda x: -x[1])
    L = [f"🗓 {label} 섹터 리포트 — {d} 기준", "", f"[{label} ETF 수익률 랭킹]"]
    for i, (name, r) in enumerate(perf, 1):
        arrow = "🔺" if r > 0 else ("🔻" if r < 0 else "▪️")
        L.append(f"{i:>2}. {name} {arrow} {r:+.2f}%")
    return "\n".join(L)


def periodic_performance(groups, days: int):
    """groups의 각 ETF에 대해 최근 days 캘린더일 수익률 계산"""
    out = []
    for gname, series in groups:
        if gname == "지수":
            continue
        for name, df in series:
            cutoff = df.index[-1] - dt.timedelta(days=days)
            past = df[df.index <= cutoff]
            base = past["종가"].iloc[-1] if len(past) else df["종가"].iloc[0]
            out.append((name, (df["종가"].iloc[-1] / base - 1) * 100))
    return out
