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

    # Virtual Scroll 対応：スクロールしながら昨日の投稿を収集する
    # Virtual DOM はスクロール位置付近の投稿しか保持しないため、
    # スクロールのたびに可視投稿を収集してdeduplicationする
    seen_posts: dict[tuple, Post] = {}
    prev_last_date = None
    no_progress_count = 0

    for scroll_count in range(60):  # 最大60回（約2.5分）
        items = page.query_selector_all("article.is_all")
        current_last_date = None

        for item in items:
            try:
                info_el = item.query_selector(".post_info")
                raw_time = info_el.inner_text().strip() if info_el else ""
                posted_at = _parse_time(raw_time)
                if posted_at is None:
                    continue

                current_last_date = posted_at.date()

                # 昨日の投稿なら収集（キーで重複排除）
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
            except Exception as e:
                print(f"[scraper]   エラー: {e}")
                continue

        print(f"[scraper] {room_id}: スクロール{scroll_count + 1}回目 "
              f"可視={len(items)}件 最新日={current_last_date} 収集={len(seen_posts)}件")

        # 昨日以降の日付に到達したら終了
        if current_last_date and current_last_date >= yesterday:
            print(f"[scraper] {room_id}: 昨日の日付に到達、スクロール終了")
            break

        # 日付が3回連続で進まなければチャット末尾と判断して終了
        if current_last_date == prev_last_date:
            no_progress_count += 1
            if no_progress_count >= 3:
                print(f"[scraper] {room_id}: 日付が進まないため終了")
                break
        else:
            no_progress_count = 0
        prev_last_date = current_last_date

        # 下にスクロールして新しい投稿を読み込む
        page.evaluate("""
            const el = document.querySelector('article.is_all');
            if (el) {
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    if (parent.scrollHeight > parent.clientHeight) {
                        parent.scrollTop = parent.scrollHeight;
                        break;
                    }
                    parent = parent.parentElement;
                }
            }
            window.scrollTo(0, document.body.scrollHeight);
        """)
        page.wait_for_timeout(2500)

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
