"""
スクレイピング結果を Google Gemini API で日本語要約する。
"""

import os
import json
import time
from datetime import datetime, timedelta, timezone

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from dotenv import load_dotenv

load_dotenv()

JST = timezone(timedelta(hours=9))

ROOMS = [
    {"title": "学長マガジン",       "room_id": "President-Tweet"},
    {"title": "学長ライブまとめ",   "room_id": "LIVE-Text"},
    {"title": "運営からのお知らせ", "room_id": "Liberal-City"},
]

SYSTEM_PROMPT = """\
あなたはオンラインコミュニティ「リベシティ」の日次ダイジェスト編集者です。
チャットルームの投稿内容を、コミュニティメンバーが素早く把握できるよう
簡潔で読みやすい日本語で要約してください。
"""

SECTION_PROMPT_TEMPLATE = """\
以下は「{title}」チャットルームの直近24時間の投稿です。
投稿がない場合は「本日の投稿はありませんでした」とだけ返してください。

投稿内容:
{posts_text}

上記を以下の形式で要約してください：
- 箇条書き（・）で重要ポイントを3〜7項目にまとめる
- 各項目は1〜2文で完結させる
- 専門用語は簡単な言葉に言い換える
- 投稿者名は含めなくてよい
"""

HIGHLIGHT_PROMPT_TEMPLATE = """\
以下は本日のリベシティ各チャットルームの要約です。

{summaries_text}

この内容全体を踏まえ、今日のリベシティで最も重要なトピックや学びを
3行以内（150文字以内）でハイライトとしてまとめてください。
読者が一番最初に目にする文章なので、簡潔でインパクトのある表現にしてください。
"""


def _posts_to_text(posts: list[dict]) -> str:
    if not posts:
        return "（投稿なし）"
    lines = []
    for p in posts:
        lines.append(f"[{p.get('posted_at', '')}] {p.get('author', '不明')}: {p.get('body', '')}")
    return "\n".join(lines)


MODEL = "gemini-1.5-flash"   # 無料枠 1500 RPD（gemini-2.5-flash は 20 RPD）


def _call_gemini(client: genai.Client, prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            return response.text.strip()
        except genai_errors.ClientError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                print(f"[summarizer] 429レート制限、{wait}秒待機してリトライ ({attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise


def summarize(scraped: dict[str, list[dict]]) -> dict:
    """スクレイピング結果を要約してJSONデータを返す。"""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    print(f"[summarizer] モデル: {MODEL}")
    now = datetime.now(JST)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    sections = []
    summaries_for_highlight = []

    for room in ROOMS:
        rid   = room["room_id"]
        title = room["title"]
        posts = scraped.get(rid, [])

        print(f"[summarizer] 要約中: {title} ({len(posts)} 件)")

        if posts:
            posts_text = _posts_to_text(posts)
            prompt = SECTION_PROMPT_TEMPLATE.format(title=title, posts_text=posts_text)
            summary = _call_gemini(client, prompt)
        else:
            summary = "本日の投稿はありませんでした"

        sections.append({
            "title":      title,
            "room_id":    rid,
            "summary":    summary,
            "post_count": len(posts),
        })
        summaries_for_highlight.append(f"【{title}】\n{summary}")

    # ハイライト生成
    print("[summarizer] ハイライト生成中...")
    summaries_text = "\n\n".join(summaries_for_highlight)
    highlight_prompt = HIGHLIGHT_PROMPT_TEMPLATE.format(summaries_text=summaries_text)
    highlight = _call_gemini(client, highlight_prompt)

    return {
        "date":         yesterday,
        "generated_at": now.isoformat(),
        "highlight":    highlight,
        "sections":     sections,
    }


if __name__ == "__main__":
    # テスト用：ダミーデータで要約
    dummy = {rid: [] for room in ROOMS for rid in [room["room_id"]]}
    result = summarize(dummy)
    print(json.dumps(result, ensure_ascii=False, indent=2))
