# Tech Steering — ICLR 2026 Topic Explorer

## システム全体構成（2 層）

**ビルドパイプライン**（Python、オフライン実行）→ 静的ファイル → **GitHub Pages**（静的配信）

ブラウザからのリアルタイム API 通信は発生しない。

| レイヤ | 技術スタック | 役割 |
|--------|------------|------|
| データ取得 | Python 3.11 + openreview-py 2.x | OpenReview API v2 から採択論文を取得 |
| Phylogeny 分類 | Python 3.11（keyword matching） | キーワードマッチング（API 不要、ローカル実行） |
| JSON 生成 | Python 3.11 + pandas | papers.json / topics.json / phylogeny.json を生成 |
| フロントエンド | **Vanilla JS + Chart.js + wordcloud2.js** | 単一 HTML ファイル（React なし、ビルドツールなし） |
| ホスティング | GitHub Pages（`docs/` ブランチ） | 静的 CDN 配信 |

## ビルドパイプライン（Python）

- **Python バージョン**: 3.13（uv が自動管理）
- **パッケージ管理**: uv（pyproject.toml + uv.lock）
- **主要ライブラリ**: `openreview-py`、`pandas`、`pydantic`
- **Gemini API**: 当初予定したが、無償枠制限により **使用中止**。分類はローカルキーワードマッチングに変更。

## OpenReview API 仕様

| 項目 | 実測値 |
|------|--------|
| Base URL | `https://api2.openreview.net` |
| Invitation | `ICLR.cc/2026/Conference/-/Submission` |
| venueid フィルタ | `content.venueid=ICLR.cc/2026/Conference`（採択論文のみ取得） |
| 認証 | 不要（匿名アクセス） |
| 採択判定 | `note.content.venueid.value == venue_id`（Decision ノードは使わない） |
| ステータス判定 | `note.content.venue.value`（例: "ICLR 2026 Oral"） |
| Rating | `directReplies` の `parentInvitations` に `Official_Review` を含むノードの `content.rating.value` |
| 取得件数 | 5,352 件（Oral: 224 / Poster: 5,128） |

## Phylogeny 分類アルゴリズム

- **アプローチ**: キーワードマッチング（`scripts/classify_phylogeny.py`）
- **スコアリング**: Domain keywords × 5.0 / Task keywords × 3.0 / Method keywords × 1.0
- **原則**: Task/Domain first（CVPR Explorer の methodology に準拠）
- **Multi-label**: 1 論文に最大 3 タグ、異なる Phylum から選択（多様性確保）
- **100% coverage**: スコア 0 の論文は "Benchmark/Dataset" または "Machine Learning" catch-all へ
- **再分類手順**: `data/phylogeny.json` を編集 → `uv run scripts/classify_phylogeny.py` → `uv run scripts/build_json.py`

## フロントエンド技術スタック

| ライブラリ | バージョン | 用途 | CDN |
|-----------|----------|------|-----|
| Chart.js | 4.4.1 | 棒グラフ・ドーナツチャート | jsdelivr |
| wordcloud2.js | 1.1.0 | フレーズワードクラウド | cdnjs |

- **React / Babel / Recharts は使用していない**（当初スペックから変更）
- フロントエンドは `docs/index.html` の単一ファイルで完結（Vanilla JS）
- フィルタ・検索・ページネーションはすべてブラウザ内 JS で処理

## セキュリティ

- 公開 JSON に個別レビュアースコア・reviewer ID を含めない
- 外部リンクに `rel="noopener noreferrer"` を付与
- XSS 対策: `escHtml()` で全ユーザー表示文字列をエスケープ（innerHTML 直書きなし）

## 保守性

- Phylogeny 定義は `data/phylogeny.json` の keywords を編集するだけで再分類可能
- 年度切り替えは `DEFAULT_VENUE_ID` 定数の変更のみ
- データ更新フロー: `classify_phylogeny.py` → `build_json.py` → `git push`（Pages 自動更新）
