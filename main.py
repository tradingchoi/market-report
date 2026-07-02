# -*- coding: utf-8 -*-
"""데일리/주간/월간 마켓 리포트 — 메인 실행 파일

사용법:
  python main.py            # 오늘 기준 자동 (평일=데일리, 금요일엔 주간 추가, 월말엔 월간 추가)
  python main.py daily      # 데일리만
  python main.py weekly     # 주간만
  python main.py monthly    # 월간만
"""
import calendar
import datetime as dt
import sys

import collectors
import charts
import report
import publishers


def is_last_business_day_of_month(date_str: str) -> bool:
    d = dt.datetime.strptime(date_str, "%Y%m%d")
    last = calendar.monthrange(d.year, d.month)[1]
    for day in range(last, d.day - 1, -1):
        cand = d.replace(day=day)
        if cand.weekday() < 5:  # 주말 제외 (공휴일은 KRX 영업일로 이미 걸러짐)
            return cand.day == d.day
    return False


def run():
    arg = sys.argv[1] if len(sys.argv) > 1 else "auto"
    date = collectors.latest_business_day()
    print(f"기준일: {date}")

    modes = []
    if arg == "auto":
        modes.append("daily")
        if dt.datetime.strptime(date, "%Y%m%d").weekday() == 4:
            modes.append("weekly")
        if is_last_business_day_of_month(date):
            modes.append("monthly")
    else:
        modes.append(arg)

    # ---- 공통 수집 (차트 데이터는 한 번만)
    groups, alignments = collectors.collect_etf_data(date)
    chart_paths = charts.draw_all(groups, date)

    if "daily" in modes:
        deposits = collectors.collect_deposits(date)
        flows = collectors.collect_investor_flows(date)
        tops, limit_ups = collectors.collect_top_value_and_limit_up(date)
        new_highs = collectors.collect_52w_new_highs()

        text = report.build_daily_text(
            date, alignments, deposits, flows, tops, limit_ups, new_highs)
        print(text)
        publishers.publish_telegram(text, chart_paths)
        publishers.publish_notion(
            f"데일리 {date[:4]}.{date[4:6]}.{date[6:]}", text, chart_paths)

    for mode, days in (("weekly", 7), ("monthly", 31)):
        if mode in modes:
            perf = report.periodic_performance(groups, days)
            text = report.build_periodic_text(mode, date, perf)
            print(text)
            publishers.publish_telegram(text, [])
            label = "주간" if mode == "weekly" else "월간"
            publishers.publish_notion(
                f"{label} {date[:4]}.{date[4:6]}.{date[6:]}", text, [])

    print("완료")


if __name__ == "__main__":
    run()
