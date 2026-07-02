# -*- coding: utf-8 -*-
"""발행 모듈 — 텔레그램 봇 + 노션 데이터베이스"""
import os

import requests

import config

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB = os.environ.get("NOTION_DATABASE_ID", "")
# 차트 이미지를 노션에 넣기 위한 GitHub raw URL prefix
# 예: https://raw.githubusercontent.com/<유저>/<레포>/main
GITHUB_RAW_BASE = os.environ.get("GITHUB_RAW_BASE", "")


# ---------------------------------------------------------------- Telegram
def tg_send_text(text: str):
    if not TG_TOKEN:
        print("[스킵] TELEGRAM_BOT_TOKEN 없음")
        return
    # 4096자 제한 → 분할 전송
    for i in range(0, len(text), config.TG_MAX_LEN):
        chunk = text[i:i + config.TG_MAX_LEN]
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": chunk},
            timeout=30,
        )
        if not r.ok:
            print(f"[경고] 텔레그램 텍스트 실패: {r.text[:200]}")


def tg_send_photo(path: str, caption: str = ""):
    if not TG_TOKEN:
        return
    with open(path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
            data={"chat_id": TG_CHAT, "caption": caption[:1000]},
            files={"photo": f},
            timeout=60,
        )
    if not r.ok:
        print(f"[경고] 텔레그램 사진 실패: {r.text[:200]}")


def publish_telegram(text: str, chart_paths: list):
    for gname, path in chart_paths:
        tg_send_photo(path, caption=gname)
    tg_send_text(text)


# ---------------------------------------------------------------- Notion
def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _text_blocks(text: str):
    """노션 paragraph 블록 (2000자 제한 대응 분할)"""
    blocks = []
    for line_group in [text[i:i + 1900] for i in range(0, len(text), 1900)]:
        blocks.append({
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": line_group}}]},
        })
    return blocks


def publish_notion(title: str, text: str, chart_paths: list):
    if not NOTION_TOKEN or not NOTION_DB:
        print("[스킵] NOTION_TOKEN / NOTION_DATABASE_ID 없음")
        return
    children = []
    # 차트 이미지: 레포에 커밋된 파일의 raw URL 임베드
    if GITHUB_RAW_BASE:
        for gname, path in chart_paths:
            url = f"{GITHUB_RAW_BASE}/{path.replace(os.sep, '/')}"
            children.append({
                "object": "block", "type": "image",
                "image": {"type": "external", "external": {"url": url}},
            })
    children.extend(_text_blocks(text))

    payload = {
        "parent": {"database_id": NOTION_DB},
        "properties": {
            "이름": {"title": [{"text": {"content": title}}]},
        },
        "children": children[:100],  # Notion API 한 번에 100블록 제한
    }
    r = requests.post("https://api.notion.com/v1/pages",
                      headers=_notion_headers(), json=payload, timeout=30)
    if not r.ok:
        # 데이터베이스 제목 속성명이 '이름'이 아닐 수 있음 → 'Name'으로 재시도
        payload["properties"] = {"Name": {"title": [{"text": {"content": title}}]}}
        r = requests.post("https://api.notion.com/v1/pages",
                          headers=_notion_headers(), json=payload, timeout=30)
    if not r.ok:
        print(f"[경고] 노션 발행 실패: {r.text[:300]}")
    else:
        print("노션 발행 완료")
