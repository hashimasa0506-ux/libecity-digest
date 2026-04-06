"""
libecity.com の3チャットルームをPlaywrightでスクレイピングする。
直近24時間以内の投稿を取得して返す。
"""

import os
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

JST = timezone(timedelta(hours=9))

ROOMS = [
    {"title": "学長マガジン",       "room_id": "President-Tweet"},
    {"title": "学長ライブまとめ",   "room_id": "LIVE-Text"},
    {"title": "運営からのお知らせ", "room_id": "Liberal-City"},
]

LOGIN_URL = "https://libecity.com/sign_in"
ROOM_URL  = "https://libecity.com/room_list?room_id={room_id}"


@dataclass
class Post:
    author: str
    posted_at: str   # ISO 8601
    body: str


def _parse_time(raw: str) -> datetime | None:
    """チャット欄に表示される時刻文字列をdatetimeに変換する。"""
    raw = raw.strip()
    now = datetime.now(JST)
    # "YYYY/MM/DD HH:MM" 形式（libecityの標準形式）
    m = re.search(r"(\d{4})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})", raw)
    if m:
        return now.replace(year=int(m.group(1)), month=int(m.group(2)),
                           day=int(m.group(3)), hour=int(m.group(4)),
                           minute=int(m.group(5)), second=0, microsecond=0)
    # "HH:MM" 形式（当日）
    m = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if m:
        return now.replace(hour=int(m.group(1)), minute=int(m.group(2)),
                           second=0, microsecond=0)
    # "M月D日 HH:MM" 形式
    m = re.match(r"^(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})$", raw)
    if m:
        return now.replace(month=int(m.group(1)), day=int(m.group(2)),
                           hour=int(m.group(3)), minute=int(m.group(4)),
                           second=0, microsecond=0)
    return None


def _login(page, email: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    # Reactアプリの描画を待つ
    page.wait_for_timeout(3000)

    # ログインフォームの入力
    page.wait_for_selector('input[placeholder="メールアドレス"]', timeout=20000)
    page.fill('input[placeholder="メールアドレス"]', email)
    page.fill('input[placeholder="パスワード"]', password)
    page.get_by_role("button", name="ログイン").click()

    page.wait_for_timeout(5000)
    print(f"[scraper] ログイン後URL: {page.url}")

    # まだログインページにいる場合はエラー
    if "sign_in" in page.url:
        raise RuntimeError(f"ログイン失敗。現在のURL: {page.url}\nページ内容:\n{page.content()[:1000]}")

    # ウェルカムモーダルを閉じる（出た場合）
    try:
        skip_btn = page.get_by_text("案内を見ずにリベシティを使う")
        skip_btn.wait_for(timeout=5000)
        skip_btn.click()
        print("[scraper] ウェルカムモーダルを閉じました")
    except PlaywrightTimeoutError:
        pass  # モーダルが出ない場合はスキップ


def _scrape_room(page, room_id: str) -> list[Post]:
    url = ROOM_URL.format(room_id=room_id)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # チャット投稿（article.is_all）が現れるまで最大30秒待機
    try:
        page.wait_for_selector("article.is_all", timeout=30000)
    except PlaywrightTimeoutError:
        print(f"[scraper] 警告: article.is_all が見つかりません ({room_id})")
        return []

    # 追加の読み込みをトリガーするためスクロール操作
    page.evaluate("""
        // メインチャットエリアを下までスクロール
        const containers = document.querySelectorAll(
            '.chatLog, .chat_wrap, .room_content, .chatPage_wrap, .js_chatArea'
        );
        containers.forEach(c => { c.scrollTop = c.scrollHeight; });
        window.scrollTo(0, document.body.scrollHeight);
    """)
    page.wait_for_timeout(3000)

    # ローディングスピナーが消えるまで待機（最大10秒）
    try:
        page.wait_for_selector(".spinner-border", state="hidden", timeout=10000)
    except PlaywrightTimeoutError:
        pass

    # 最終レンダリング待ち
    page.wait_for_timeout(2000)

    # 投稿要素を取得（article.is_all が1投稿に対応）
    items = page.query_selector_all("article.is_all")
    print(f"[scraper] {room_id}: {len(items)} 件の要素を検出")
    if not items:
        return []

    # 「昨日の0時〜23時59分」の投稿を全て取得
    now = datetime.now(JST)
    yesterday = (now - timedelta(days=1)).date()
    day_start = datetime(yesterday.year, yesterday.month, yesterday.day,
                         0, 0, 0, tzinfo=JST)
    day_end   = datetime(yesterday.year, yesterday.month, yesterday.day,
                         23, 59, 59, tzinfo=JST)

    posts: list[Post] = []

    for item in items:
        try:
            # 投稿者名：.post_user
            author_el = item.query_selector(".post_user")
            author = author_el.inner_text().strip() if author_el else "不明"

            # 投稿時刻：.post_info 内の "YYYY/MM/DD HH:MM" 形式
            info_el = item.query_selector(".post_info")
            raw_time = info_el.inner_text().strip() if info_el else ""
            posted_at = _parse_time(raw_time)

            # デバッグ：各投稿の日時を出力
            print(f"[scraper]   raw_time={repr(raw_time[:40])} → posted_at={posted_at}")

            if posted_at is None:
                continue  # 日時不明の投稿はスキップ

            if not (day_start <= posted_at <= day_end):
                continue  # 昨日以外はスキップ

            # 本文：.post_text
            body_el = item.query_selector(".post_text")
            body = body_el.inner_text().strip() if body_el else ""

            if body:
                posts.append(Post(
                    author=author,
                    posted_at=posted_at.isoformat(),
                    body=body,
                ))
        except Exception as e:
            print(f"[scraper]   エラー: {e}")
            continue

    return posts


def scrape_all(headless: bool = True) -> dict[str, list[dict]]:
    """全ルームをスクレイピングして {room_id: [post_dict, ...]} を返す。"""
    email    = os.environ["LIBECITY_EMAIL"]
    password = os.environ["LIBECITY_PASSWORD"]

    results: dict[str, list[dict]] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )
        page = context.new_page()

        _login(page, email, password)

        for room in ROOMS:
            rid = room["room_id"]
            print(f"[scraper] スクレイピング中: {room['title']} ({rid})")
            posts = _scrape_room(page, rid)
            results[rid] = [asdict(p) for p in posts]
            print(f"[scraper]  → {len(posts)} 件取得")

        browser.close()

    return results


if __name__ == "__main__":
    import json
    data = scrape_all(headless=False)
    print(json.dumps(data, ensure_ascii=False, indent=2))
