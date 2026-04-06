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

    now = datetime.now(JST)
    yesterday = (now - timedelta(days=1)).date()
    day_start = datetime(yesterday.year, yesterday.month, yesterday.day,
                         0, 0, 0, tzinfo=JST)
    day_end   = datetime(yesterday.year, yesterday.month, yesterday.day,
                         23, 59, 59, tzinfo=JST)

    seen_posts: dict[tuple, Post] = {}

    def collect_visible() -> tuple:
        """可視投稿から昨日分を収集し、(最古日, 最新日, 件数) を返す。"""
        items = page.query_selector_all("article.is_all")
        first_date = last_date = None
        for item in items:
            try:
                info_el = item.query_selector(".post_info")
                posted_at = _parse_time(info_el.inner_text().strip() if info_el else "")
                if posted_at is None:
                    continue
                if first_date is None:
                    first_date = posted_at.date()
                last_date = posted_at.date()
                if day_start <= posted_at <= day_end:
                    author_el = item.query_selector(".post_user")
                    author = author_el.inner_text().strip() if author_el else "不明"
                    body_el = item.query_selector(".post_text")
                    body = body_el.inner_text().strip() if body_el else ""
                    if body:
                        key = (author, posted_at.isoformat())
                        seen_posts[key] = Post(
                            author=author,
                            posted_at=posted_at.isoformat(),
                            body=body,
                        )
            except Exception:
                continue
        return first_date, last_date, len(items)

    def do_scroll(direction: str) -> None:
        """direction='down' or 'up'"""
        if direction == "down":
            js = """
                const el = document.querySelector('article.is_all');
                if (el) {
                    let p = el.parentElement;
                    while (p && p !== document.body) {
                        if (p.scrollHeight > p.clientHeight) { p.scrollTop = p.scrollHeight; break; }
                        p = p.parentElement;
                    }
                }
                window.scrollTo(0, document.body.scrollHeight);
            """
        else:
            js = """
                const el = document.querySelector('article.is_all');
                if (el) {
                    let p = el.parentElement;
                    while (p && p !== document.body) {
                        if (p.scrollHeight > p.clientHeight) { p.scrollTop = 0; break; }
                        p = p.parentElement;
                    }
                }
                window.scrollTo(0, 0);
            """
        page.evaluate(js)
        page.wait_for_timeout(2500)

    # ── Phase 1 (DOWN) ──────────────────────────────────────────────
    # 初期表示が昨日より古い場合に下スクロールで昨日まで到達する
    prev_last = None
    no_prog = 0
    for i in range(60):
        fd, ld, cnt = collect_visible()
        print(f"[scraper] {room_id}: DOWN {i+1}回目 可視={cnt}件 "
              f"最古={fd} 最新={ld} 収集={len(seen_posts)}件")
        if ld is None or ld >= yesterday:
            break
        if ld == prev_last:
            no_prog += 1
            if no_prog >= 3:
                print(f"[scraper] {room_id}: DOWN 進捗なし、打ち切り")
                break
        else:
            no_prog = 0
        prev_last = ld
        do_scroll("down")

    # ── Phase 2 (UP) ────────────────────────────────────────────────
    # 昨日の投稿の先頭（= 前日以前の投稿が見えるまで）を上スクロールで探す
    prev_first = None
    no_prog = 0
    for i in range(60):
        fd, ld, cnt = collect_visible()
        print(f"[scraper] {room_id}: UP {i+1}回目 可視={cnt}件 "
              f"最古={fd} 最新={ld} 収集={len(seen_posts)}件")
        if fd is None or fd < yesterday:
            print(f"[scraper] {room_id}: 昨日より前の投稿に到達、終了")
            break
        if fd == prev_first:
            no_prog += 1
            if no_prog >= 3:
                print(f"[scraper] {room_id}: UP 進捗なし、打ち切り")
                break
        else:
            no_prog = 0
        prev_first = fd
        do_scroll("up")

    print(f"[scraper] {room_id}: 合計 {len(seen_posts)} 件取得")
    return list(seen_posts.values())


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
