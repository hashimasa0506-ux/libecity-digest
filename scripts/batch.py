"""
スクレイピング → 要約 → JSON保存 を一括実行するエントリポイント。
GitHub Actions または手動実行で使用する。
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# プロジェクトルートを sys.path に追加（scriptsディレクトリから実行した場合対応）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from scraper import scrape_all
from summarizer import summarize

JST = timezone(timedelta(hours=9))
DATA_DIR = ROOT / "data" / "summaries"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("[batch] スクレイピング開始")
    scraped = scrape_all(headless=True)

    print("[batch] 要約開始")
    result = summarize(scraped)

    date_str  = result["date"]
    out_path  = DATA_DIR / f"{date_str}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[batch] 保存完了: {out_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
