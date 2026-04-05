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

    # デバッグ用スクリーンショット
    page.screenshot(path="/tmp/login_page.png", full_page=True)

    # ログインフォームの入力（スクリーンショットで確認したプレースホルダーを使用）
    page.wait_for_selector('input[placeholder="メールアドレス"]', timeout=20000)
    page.fill('input[placeholder="メールアドレス"]', email)
    page.fill('input[placeholder="パスワード"]', password)
    page.get_by_role("button", name="ログイン").click()

    # ログイン後の状態を記録
    page.wait_for_timeout(5000)
    page.screenshot(path="/tmp/after_login.png", full_page=True)
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

    # チャットコンテナが現れるまで待機
    try:
        page.wait_for_selector(".content_chatlog", timeout=20000)
    except PlaywrightTimeoutError:
        print(f"[scraper] 警告: .content_chatlog が見つかりません ({room_id})")
        page.screenshot(path=f"/tmp/room_{room_id}.png", full_page=True)
        return []

    # v3-infinite-loading を起動させるためにスクロール操作
    # チャットコンテナ内をスクロールして投稿読み込みをトリガー
    page.evaluate("""
        const container = document.querySelector('.content_chatlog');
        if (container) {
            container.scrollTop = container.scrollHeight;
        } else {
            window.scrollTo(0, document.body.scrollHeight);
        }
    """)
    page.wait_for_timeout(3000)

    # さらに上にスクロール（最新投稿が上の場合）
    page.evaluate("""
        const container = document.querySelector('.content_chatlog');
        if (container) { container.scrollTop = 0; }
        else { window.scrollTo(0, 0); }
    """)
    page.wait_for_timeout(3000)

    # ローディングスピナーが消えるまで待機（最大15秒）
    try:
        page.wait_for_selector(".spinner-border", state="hidden", timeout=15000)
    except PlaywrightTimeoutError:
        pass

    # Vue.jsのレンダリング完了を待つ
    page.wait_for_timeout(3000)

    # デバッグ用：スクリーンショットとHTMLを保存
    page.screenshot(path=f"/tmp/room_{room_id}.png", full_page=True)
    with open(f"/tmp/room_{room_id}.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    # メッセージ一覧の確認
    items_check = page.query_selector_all("article.tweet_log")
    print(f"[scraper] {room_id}: article.tweet_log = {len(items_check)} 件")
    if not items_check:
        return []

    cutoff = datetime.now(JST) - timedelta(hours=24)
    posts: list[Post] = []

    # libecity の実際のDOM構造に基づくセレクタ
    # article.tweet_log が1投稿に対応する
    items = page.query_selector_all("article.tweet_log")
    print(f"[scraper] {room_id}: {len(items)} 件の要素を検出")

    for item in items:
        try:
            # 投稿者名：.username
            author_el = item.query_selector(".username")
            author = author_el.inner_text().strip() if author_el else "不明"

            # 投稿時刻：.date_btn_box 内のテキスト
            time_el = item.query_selector(".date_btn_box, .form_date_title")
            raw_time = time_el.inner_text().strip() if time_el else ""
            posted_at = _parse_time(raw_time)
            if posted_at is None:
                try:
                    posted_at = datetime.fromisoformat(raw_time).astimezone(JST)
                except (ValueError, TypeError):
                    posted_at = datetime.now(JST)

            if posted_at < cutoff:
                continue

            # 本文：.text_block
            body_el = item.query_selector(".text_block, .text")
            body = body_el.inner_text().strip() if body_el else item.inner_text().strip()

            if body:
                posts.append(Post(
                    author=author,
                    posted_at=posted_at.isoformat(),
                    body=body,
                ))
        except Exception:
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
