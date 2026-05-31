# Structure Steering — ICLR 2026 Topic Explorer

## ディレクトリ構成

```
iclr-explorer/
├── pyproject.toml               # uv プロジェクト定義
├── uv.lock
├── README.md
│
├── scripts/                     # ビルドパイプライン（Python）
│   ├── fetch_papers.py          # F-01: OpenReview API からデータ取得
│   ├── classify_topics.py       # F-02: Claude API でトピック分類
│   └── build_json.py            # F-03: 静的 JSON 生成
│
├── data/                        # 取得・処理データ（Git 管理対象）
│   ├── papers_raw.json          # OpenReview から取得した生データ
│   ├── papers_classified.json   # トピック分類済みデータ
│   └── topics.json              # トピック定義・統計
│
└── docs/                        # GitHub Pages 公開ルート
    ├── index.html               # SPA エントリポイント（単一ファイル）
    └── data/ -> ../data/        # シンボリックリンクまたはコピー
        ├── papers.json          # 分類済み論文データ（配信用）
        └── topics.json          # トピック定義・統計
```

## データフロー

```
OpenReview API
      ↓ fetch_papers.py
data/papers_raw.json（~5,343 件）
      ↓ classify_topics.py（Claude API、50 件バッチ）
data/papers_classified.json
      ↓ build_json.py
docs/data/papers.json（配信用、UI 最適化）
docs/data/topics.json（トピック定義）
      ↓ GitHub Pages
公開 URL
```

## ファイル名・命名規則

- スクリプト: `動詞_名詞.py` の snake_case（`fetch_papers.py`, `classify_topics.py`, `build_json.py`）
- データファイル: 処理段階を示す名前（`papers_raw` → `papers_classified` → `papers`）
- トピック ID: `T-01`〜`T-15+` の形式（topics.json で定義）
- HTML: 単一ファイル `index.html`

## データスキーマ

### papers.json（配信用）

```json
{
  "meta": {
    "generated_at": "2026-05-30T00:00:00Z",
    "total_papers": 5343,
    "model_used": "claude-sonnet-4-20250514"
  },
  "papers": [{
    "id": "openreview_id",
    "title": "論文タイトル",
    "authors": ["著者1", "著者2"],
    "abstract": "アブストラクト本文（CC0）",
    "keywords": ["keyword1", "keyword2"],
    "status": "Poster | Oral",
    "rating_avg": 6.25,
    "primary_topic": "T-01",
    "secondary_topics": ["T-08"],
    "openreview_url": "https://openreview.net/forum?id=..."
  }]
}
```

### topics.json（トピック定義）

```json
{
  "topics": [{
    "id": "T-01",
    "name": "Large Language Models",
    "name_ja": "大規模言語モデル",
    "description": "LLM, instruction tuning, RLHF, alignment ...",
    "color": "#4FB6C6",
    "paper_count": 842
  }]
}
```

## スクリプト設計原則

- **単一責任**: 取得 / 分類 / 変換 を別スクリプトに分離
- **冪等性（べき等性）**: 再実行してもデータが壊れない（キャッシュ・スキップ機構）
  - `papers_raw.json` が存在する場合は取得をスキップ（FR-01-5）
  - 分類済みエントリは再処理しない checkpoint 機構（FR-02-6）
- **スリープ**: OpenReview API リクエスト間に 0.5 秒待機（FR-01-4）
- 各スクリプト末尾に `if __name__ == "__main__":` ブロック

## .gitignore パターン

- `__pycache__/`, `*.pyc`
- `.env`（使用する場合）
- `data/` は**Git 管理対象**（静的サイトのデータソース）
- `docs/data/` がシンボリックリンクの場合はリンク先の `data/` を管理

## 受入基準（AC）

| 基準 ID | 条件 |
|---------|------|
| AC-01 | papers.json に 5,000 件以上が含まれ、全件に primary_topic が付与されていること |
| AC-02 | GitHub Pages の URL にアクセスし、トップページが 3 秒以内に表示されること |
| AC-03 | トピックフィルタで 1 トピックを選択した際、該当論文のみ一覧に表示されること |
| AC-04 | 「LLM」等のキーワードで検索した際、タイトルまたはアブストラクトに含む論文が表示されること |
| AC-05 | 論文カードから OpenReview のリンクをクリックし、対応する論文ページに遷移できること |
| AC-06 | モバイルブラウザ（iOS Safari / Android Chrome）でレイアウトが崩れないこと |
| AC-07 | papers.json / topics.json が docs/ 配下に存在し、index.html から fetch できること |
