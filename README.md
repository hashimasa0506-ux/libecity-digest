# リベシティ 日次ダイジェスト

リベシティ（libecity.com）の3つのチャットルームを毎朝自動スクレイピングし、Claude AIで要約してVercel上に表示するWebアプリです。

## アーキテクチャ

```
GitHub Actions (毎朝7時JST)
  └─ Playwright でスクレイピング
  └─ Claude API で日本語要約
  └─ data/summaries/YYYY-MM-DD.json を git push

Vercel
  └─ Next.js 14 App Router
  └─ data/summaries/ を静的読み込みして表示
```

---

## 1. GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から以下の3つを登録してください。

| Secret 名 | 内容 |
|---|---|
| `LIBECITY_EMAIL` | リベシティのログインメールアドレス |
| `LIBECITY_PASSWORD` | リベシティのログインパスワード |
| `ANTHROPIC_API_KEY` | Anthropic API キー（`sk-ant-...`） |

---

## 2. Vercel へのデプロイ手順

### 前提
- GitHub リポジトリに push 済みであること
- Vercel アカウントを持っていること

### 手順

1. [vercel.com/new](https://vercel.com/new) にアクセス
2. **「Import Git Repository」** からこのリポジトリを選択
3. Framework Preset が **Next.js** であることを確認
4. **「Deploy」** をクリック

> **注意：** `next.config.mjs` で `output: "export"` を設定しているため、
> Vercel は静的サイトとしてビルドします。
> GitHub Actions が JSON を push するたびに Vercel が自動的に再ビルドされます。

---

## 3. ローカルで batch.py を手動実行する方法

### セットアップ

```bash
# 1. Python 依存関係をインストール
cd scripts
pip install -r requirements.txt

# 2. Playwright の Chromium をインストール
python -m playwright install chromium

# 3. .env ファイルを作成
cp ../.env.example ../.env
# .env を編集して3つの値を設定
```

### .env ファイルの内容

```
LIBECITY_EMAIL=your_email@example.com
LIBECITY_PASSWORD=your_password
ANTHROPIC_API_KEY=sk-ant-...
```

### 実行

```bash
# プロジェクトルートから実行
cd ~/libecity-digest
python scripts/batch.py
```

実行後、`data/summaries/YYYY-MM-DD.json` が生成されます。

### Next.js を起動して確認

```bash
npm install
npm run dev
# http://localhost:3000 で確認
```

---

## ファイル構成

```
libecity-digest/
├── .github/workflows/scrape.yml   # GitHub Actions（毎日22:00 UTC）
├── scripts/
│   ├── scraper.py                 # Playwrightスクレイピング
│   ├── summarizer.py              # Claude API要約
│   ├── batch.py                   # 一括実行エントリポイント
│   └── requirements.txt
├── data/summaries/                # 日次JSONが蓄積される
├── src/
│   ├── app/
│   │   ├── page.tsx               # トップ（最新要約）
│   │   ├── history/page.tsx       # 履歴一覧
│   │   └── summary/[date]/page.tsx # 日付別詳細
│   ├── components/SummaryView.tsx # 要約表示コンポーネント
│   └── lib/summaries.ts           # JSONファイル読み込みユーティリティ
├── .env.example
└── package.json
```
