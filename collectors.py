# -*- coding: utf-8 -*-
"""데이터 수집 모듈 (KRX / 네이버금융 / 금투협)"""
import datetime as dt
import json
import re
import time

import pandas as pd
import requests
from pykrx import stock

import config

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ---------------------------------------------------------------- 공통
def latest_business_day() -> str:
    """가장 최근 영업일(YYYYMMDD). 장 마감 후 실행 기준."""
    today = dt.datetime.now().strftime("%Y%m%d")
    return stock.get_nearest_business_day_in_a_week(today)


def _norm(name: str) -> str:
    """ETF 이름 비교용 정규화(공백/기호 제거, 대문자화)"""
    return re.sub(r"[\s&\-_]", "", name).upper()


# ---------------------------------------------------------------- ETF
_ETF_NAME_CACHE = None


def resolve_etf_tickers(names, date) -> dict:
    """설정에 적은 ETF 이름 -> (티커, 정식명칭) 매핑. 부분일치 허용."""
    global _ETF_NAME_CACHE
    if _ETF_NAME_CACHE is None:
        tickers = stock.get_etf_ticker_list(date)
        _ETF_NAME_CACHE = {t: stock.get_etf_ticker_name(t) for t in tickers}
    result = {}
    for want in names:
        w = _norm(want)
        found = None
        for t, real in _ETF_NAME_CACHE.items():
            r = _norm(real)
            if r == w or w in r or r in w:
                found = (t, real)
                if r == w:
                    break
        result[want] = found  # 못 찾으면 None
    return result


def fetch_ohlcv(ticker: str, end_date: str, is_index=False) -> pd.DataFrame:
    """종가 시계열 + 이동평균. index/ETF 공용."""
    start = (dt.datetime.strptime(end_date, "%Y%m%d")
             - dt.timedelta(days=config.CHART_LOOKBACK_DAYS + 120)).strftime("%Y%m%d")
    if is_index:
        df = stock.get_index_ohlcv_by_date(start, end_date, ticker)
    else:
        df = stock.get_etf_ohlcv_by_date(start, end_date, ticker)
    df = df[["종가"]].copy()
    for w in config.MA_WINDOWS:
        df[f"MA{w}"] = df["종가"].rolling(w).mean()
    cutoff = dt.datetime.strptime(end_date, "%Y%m%d") - dt.timedelta(days=config.CHART_LOOKBACK_DAYS)
    return df[df.index >= cutoff]


def classify_alignment(df: pd.DataFrame) -> str:
    """마지막 봉 기준 정배열/역배열/중립 판정"""
    last = df.iloc[-1]
    c, m5, m20, m60 = last["종가"], last["MA5"], last["MA20"], last["MA60"]
    if any(pd.isna(x) for x in (c, m5, m20, m60)):
        return "판정불가"
    vals = [m5, m20, m60]
    spread = (max(vals) - min(vals)) / m20
    if spread < 0.01:
        return "중립/걸침"
    if c > m5 > m20 > m60:
        return "정배열"
    if c < m5 < m20 < m60:
        return "역배열"
    return "혼조"


def collect_etf_data(date: str):
    """모든 그룹의 ETF 시계열 + 정배열 판정 결과.
    반환: (groups, alignments)
      groups = [(그룹명, [(표시명, df), ...]), ...]
      alignments = {"정배열": [...], "중립/걸침": [...], ...}
    """
    all_names = [n for _, names in config.ETF_GROUPS for n in names]
    mapping = resolve_etf_tickers(all_names, date)

    groups, alignments = [], {}
    for gname, names in config.ETF_GROUPS:
        series = []
        for name in names:
            hit = mapping.get(name)
            if not hit:
                print(f"[경고] ETF 못 찾음: {name}")
                continue
            ticker, real = hit
            try:
                df = fetch_ohlcv(ticker, date)
                series.append((real, df))
                alignments.setdefault(classify_alignment(df), []).append(real)
                time.sleep(0.3)  # KRX 요청 매너
            except Exception as e:
                print(f"[경고] {real} 시세 실패: {e}")
        groups.append((gname, series))

    # 지수는 첫 그룹 앞에 붙임
    idx_series = []
    for iname, iticker in config.INDICES.items():
        try:
            idx_series.append((iname, fetch_ohlcv(iticker, date, is_index=True)))
        except Exception as e:
            print(f"[경고] 지수 {iname} 실패: {e}")
    groups.insert(0, ("지수", idx_series))
    return groups, alignments


# ------------------------------------------------- 투자자별 매매동향
def collect_investor_flows(date: str) -> dict:
    """코스피/코스닥 개인·외국인·기관 순매수(억원)"""
    out = {}
    for market in ("KOSPI", "KOSDAQ"):
        try:
            df = stock.get_market_trading_value_by_investor(date, date, market)
            net = df["순매수"]
            def _pick(*keys):
                s = 0
                for k in keys:
                    if k in net.index:
                        s += net[k]
                return s
            out[market] = {
                "개인": _pick("개인") / 1e8,
                "외국인": _pick("외국인", "기타외국인") / 1e8,
                "기관": _pick("기관합계") / 1e8,
            }
        except Exception as e:
            print(f"[경고] {market} 투자자 동향 실패: {e}")
            out[market] = None
    return out


# ------------------------------------------------- 거래대금 상위 / 상한가
def collect_top_value_and_limit_up(date: str):
    tops, limit_ups = {}, {}
    for market in ("KOSPI", "KOSDAQ"):
        try:
            df = stock.get_market_ohlcv_by_ticker(date, market=market)
            df = df[df["거래대금"] > 0].copy()
            df["종목명"] = [stock.get_market_ticker_name(t) for t in df.index]
            top = df.sort_values("거래대금", ascending=False).head(config.TOP_VALUE_COUNT)
            tops[market] = [
                (r["종목명"], r["거래대금"] / 1e8, r["등락률"]) for _, r in top.iterrows()
            ]
            lu = df[df["등락률"] >= 29.5]
            limit_ups[market] = [(r["종목명"], r["등락률"]) for _, r in lu.iterrows()]
        except Exception as e:
            print(f"[경고] {market} 거래대금/상한가 실패: {e}")
            tops[market], limit_ups[market] = None, None
    return tops, limit_ups


# ------------------------------------------------- 52주 신고가 (네이버금융)
def collect_52w_new_highs():
    """네이버금융 신고가 페이지 스크래핑. 실패 시 None."""
    out = {}
    for market, sosok in (("KOSPI", 0), ("KOSDAQ", 1)):
        try:
            url = f"https://finance.naver.com/sise/sise_new_high.naver?sosok={sosok}"
            html = requests.get(url, headers=HEADERS, timeout=15).text
            names = re.findall(r'<a href="/item/main\.naver\?code=\d+"[^>]*>([^<]+)</a>', html)
            names = [n.strip() for n in names if n.strip()][: config.NEW_HIGH_MAX]
            out[market] = names or None
        except Exception as e:
            print(f"[경고] {market} 52주 신고가 실패: {e}")
            out[market] = None
    return out


# ------------------------------------------------- 고객예탁금 (금투협 FreeSIS)
def collect_deposits(date: str):
    """고객예탁금 / 신용융자잔고 (조원). D-1 데이터.
    금투협 FreeSIS 비공식 JSON API 사용 — 사이트 개편 시 수정 필요할 수 있음.
    실패 시 None 반환하고 리포트에는 '수집 실패'로 표기됨."""
    end = dt.datetime.strptime(date, "%Y%m%d")
    start = end - dt.timedelta(days=10)
    payload = {
        "dmSearch": {
            "tmpV40": "1000000000",
            "tmpV41": "1",
            "tmpV1": "12",
            "tmpV45": start.strftime("%Y%m%d"),
            "tmpV46": end.strftime("%Y%m%d"),
            "OBJ_NM": "STATSCU0100000060BO",  # 투자자예탁금 등 증시자금 추이
        }
    }
    try:
        r = requests.post(
            "https://freesis.kofia.or.kr/meta/getMetaDataList.do",
            json=payload, headers={**HEADERS, "Content-Type": "application/json"},
            timeout=20,
        )
        rows = r.json().get("ds1", [])
        if not rows:
            return None
        last = rows[-1]
        # 컬럼: TMPV1=일자, TMPV2=투자자예탁금, TMPV5=신용융자(사이트 개편 시 확인 필요)
        deposit = float(str(last.get("TMPV2", "0")).replace(",", "")) / 1e4   # 억 -> 조
        credit = float(str(last.get("TMPV5", "0")).replace(",", "")) / 1e4
        return {"일자": last.get("TMPV1"), "고객예탁금": deposit, "신용잔고": credit}
    except Exception as e:
        print(f"[경고] 고객예탁금 수집 실패: {e}")
        return None
