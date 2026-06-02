# Structure Steering — ICLR 2026 Topic Explorer

## ディレクトリ構成

```
iclr-explorer/
├── pyproject.toml               # uv プロジェクト定義
├── uv.lock
├── README.md                    # ライブデモリンク付き
│
├── scripts/                     # ビルドパイプライン（Python）
│   ├── fetch_papers.py          # OpenReview API からデータ取得
│   ├── classify_phylogeny.py    # ★主分類: 4段階 Phylogeny（API不要）
│   ├── classify_topics.py       # サブ分類（Gemini API 版、現在未使用）
│   ├── classify_topics_local.py # サブ分類（旧キーワード版、現在未使用）
│   └── build_json.py            # papers.json / topics.json / phylogeny.json 生成
│
├── data/                        # Git 管理対象
│   ├── phylogeny.json           # ★ Phylogeny 定義（キーワード含む、手動編集可）
│   ├── topics.json              # 旧 18 カテゴリ定義（互換性のため維持）
│   ├── papers_raw.json          # .gitignore 対象（大容量）
│   └── papers_classified.json  # .gitignore 対象（大容量）
│
├── docs/                        # GitHub Pages 公開ルート
│   ├── index.html               # ★ 単一ファイル SPA（Vanilla JS + Chart.js）
│   └── data/
│       ├── papers.json          # 配信用論文データ（phylogeny topics 含む）
│       ├── topics.json          # 旧トピック定義（互換性）
│       └── phylogeny.json       # ★ Phylogeny ツリー（paper_count 付き）
│
└── tests/                       # pytest テストスイート
```

## データフロー

```
OpenReview API
      ↓ fetch_papers.py
data/papers_raw.json（5,352 件・venueid フィルタで採択論文のみ）
      ↓ classify_phylogeny.py
data/papers_classified.json（topics[] フィールド付き、100% coverage）
      ↓ build_json.py
docs/data/papers.json   ← 配信用（phylogeny フィールド含む）
docs/data/phylogeny.json ← ツリー構造 + paper_count
docs/data/topics.json    ← 旧互換
      ↓ git push
https://kenkuuu.github.io/iclr-explorer/
```

## データスキーマ

### papers.json（配信用、主要フィールド）

```json
{
  "meta": { "generated_at": "...", "total_papers": 5352, "model_used": "gemini-3.5-flash" },
  "papers": [{
    "id": "openreview_id",
    "title": "...", "authors": [...], "abstract": "...(max 500 chars)",
    "keywords": [...], "status": "Oral | Poster", "rating_avg": 6.25,
    "primary_topic": "P5",
    "topics": [{"phylum":"RL","class":"RL Algorithms","order":"Policy Optimization","genus":"Policy Gradient","phylum_id":"P5","score":6.25}],
    "primary_phylum": "Reinforcement Learning",
    "openreview_url": "https://openreview.net/forum?id=..."
  }]
}
```

### phylogeny.json（4 段階ツリー）

```json
{
  "name": "ICLR 2026", "paper_count": 5352,
  "children": [{
    "id": "P1", "name": "Large Language Models", "color": "#4FB6C6", "paper_count": 1338,
    "children": [{
      "id": "C1.1", "name": "LM Pretraining & Architecture", "paper_count": 589,
      "children": [{
        "id": "O1.1.1", "name": "Architecture & Scaling", "paper_count": 330,
        "children": [{"id":"G1.1.1","name":"Pretraining / Scaling","paper_count":330,
          "domain":["scaling law","pretraining",...], "task":[...], "method":[...]}]
      }]
    }]
  }]
}
```

## 命名規則

- スクリプト: `動詞_名詞.py`（snake_case）
- Phylum ID: `P1`〜`P10`
- Class ID: `C{phylum}.{n}`（例: `C1.1`）
- 論文フィールド: snake_case（`primary_phylum`, `rating_avg`）
- JS グローバル変数: UPPER_CASE（`PAPERS`, `TREE`, `PHYLUM_COLORS`）

## フロントエンド構造（docs/index.html）

単一ファイル内の主要関数：

| 関数 | 役割 |
|------|------|
| `init()` | データロード後に全コンポーネントを初期化 |
| `buildKpis()` | 統計カード（KPI）の描画 |
| `buildWordCloud()` | wordcloud2.js でフレーズワードクラウドを描画 |
| `buildPhylumChart()` / `buildClassChart()` | Chart.js 横棒グラフ |
| `buildTree()` | Phylogeny Tree のインタラクティブ HTML を生成 |
| `showLineage(node)` | ツリーノード選択時に子ノードのバーチャートを更新 |
| `filtered()` | 3 検索欄 + 複数ドロップダウンの複合フィルタ |
| `renderResults()` | 論文カードリスト + ページネーション描画 |

## Phylogeny 再分類手順

```bash
# 1. data/phylogeny.json の keywords を編集（domain/task/method の 3 階層）
# 2. 再分類（数秒）
uv run scripts/classify_phylogeny.py --stats
# 3. 配信 JSON を再生成
uv run scripts/build_json.py
# 4. デプロイ
git add docs/data/ && git commit -m "Update classification" && git push
```

## テスト

- `uv run pytest tests/ -q`（338 テスト）
- フロントエンドテスト: HTML の構造・関数の存在を Python で確認
- バックエンドテスト: Python スクリプトのロジックを unittest/mock で確認
