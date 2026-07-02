# -*- coding: utf-8 -*-
"""차트 생성 모듈 — 그룹당 PNG 1장 (종가 + MA5/20/60)"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

import config

COLORS = {"종가": "#1a1a2e", "MA5": "#e63946", "MA20": "#f4a261", "MA60": "#2a9d8f"}


def _set_korean_font():
    for name in ("NanumGothic", "NanumBarunGothic", "Malgun Gothic", "AppleGothic"):
        if any(name in f.name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def draw_group_chart(group_name: str, series: list, date: str, out_dir: str) -> str:
    """series = [(이름, df), ...] -> PNG 경로 반환"""
    _set_korean_font()
    n = len(series)
    if n == 0:
        return None
    cols = 2
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(11, 3.4 * rows), squeeze=False)

    for i, (name, df) in enumerate(series):
        ax = axes[i // cols][i % cols]
        ax.plot(df.index, df["종가"], color=COLORS["종가"], lw=1.6, label="종가")
        for w in config.MA_WINDOWS:
            ax.plot(df.index, df[f"MA{w}"], color=COLORS[f"MA{w}"], lw=1.0, label=f"MA{w}")
        chg = (df["종가"].iloc[-1] / df["종가"].iloc[-2] - 1) * 100 if len(df) > 1 else 0
        sign = "▲" if chg > 0 else ("▼" if chg < 0 else "-")
        ax.set_title(f"{name}  {df['종가'].iloc[-1]:,.0f} {sign}{abs(chg):.2f}%", fontsize=11)
        ax.grid(alpha=0.25)
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.tick_params(labelsize=8)
        ax.legend(fontsize=7, loc="upper left")

    # 빈 서브플롯 숨김
    for j in range(n, rows * cols):
        axes[j // cols][j % cols].axis("off")

    fig.suptitle(f"{group_name}  ({date[:4]}-{date[4:6]}-{date[6:]})", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    os.makedirs(out_dir, exist_ok=True)
    safe = group_name.replace("/", "_").replace(" ", "")
    path = os.path.join(out_dir, f"{safe}.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def draw_all(groups, date: str) -> list:
    out_dir = os.path.join(config.CHART_DIR, f"{date[:4]}-{date[4:6]}-{date[6:]}")
    paths = []
    for gname, series in groups:
        p = draw_group_chart(gname, series, date, out_dir)
        if p:
            paths.append((gname, p))
    return paths
