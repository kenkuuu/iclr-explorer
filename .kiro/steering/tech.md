# Tech Steering — ICLR 2026 Topic Explorer

## システム全体構成（2 層）

本システムは「ビルドパイプライン」と「静的フロントエンド」の 2 層で構成される。ビルドパイプライン（Python）はオフラインで一度だけ実行し、生成した静的ファイルを GitHub Pages にデプロイする。ブラウザからのリアルタイム API 通信は発生しない。

| レイヤ | 技術スタック | 役割 |
|--------|------------|------|
| データ取得 | Python 3.11 + openreview-py | OpenReview API から採択論文メタデータを取得し papers_raw.json として保存 |
| トピック分類 | Python 3.11 + google-genai | 50 件バッチで Gemini API を呼び出し、各論文にトピックタグを付与 |
| データ変換 | Python 3.11（pandas） | 分類済みデータを UI 最適化 JSON（papers.json, topics.json）に変換 |
| フロントエンド | HTML + React 18（CDN）+ Recharts | 単一 HTML ファイルで構成された SPA。外部依存は CDN 読み込みのみ |
| ホスティング | GitHub Pages | 静的ファイルを無料 CDN で配信。カスタムドメイン任意 |

## ビルドパイプライン（Python）

- **Python バージョン**: 3.11
- **パッケージ管理**: uv（pyproject.toml + uv.lock）
- **主要ライブラリ**:
  - `openreview-py` — OpenReview API v2 クライアント
  - `google-genai` — Gemini API（Google Gen AI Python SDK）
  - `pandas` — データ集計・変換

## Gemini API 仕様

| 項目 | 値 |
|------|-----|
| 使用モデル | `gemini-3.5-flash` |
| バッチサイズ | 50 件 / リクエスト（プロンプト ~4,000 tokens 目安） |
| 出力形式 | structured output（JSON Schema ネイティブ、Pydantic 直接対応） |
| リトライ | エラー・タイムアウト時は最大 3 回 |
| 推定コスト | ~$0.5〜1 USD（入力 $1.50/MTok, 出力 $9.00/MTok 試算） |
| API キー管理 | GitHub Actions Secrets（`GEMINI_API_KEY`）に保管。コードに直書き禁止 |

## OpenReview API 仕様

| 項目 | 値 |
|------|-----|
| Base URL | `https://api2.openreview.net` |
| エンドポイント | `GET /notes?invitation=ICLR.cc/2026/Conference/-/Submission&details=directReplies` |
| 認証 | 不要（匿名アクセス） |
| ページネーション | offset / limit パラメータ（limit 最大 1000） |
| レート制限 | 明示なし。リクエスト間 0.5 秒スリープを自主設定 |

## フロントエンド CDN 依存

| ライブラリ | バージョン | 用途 | CDN |
|-----------|----------|------|-----|
| React | 18.x | UI コンポーネント管理 | esm.sh |
| ReactDOM | 18.x | DOM レンダリング | esm.sh |
| Recharts | 2.x | チャート・グラフ描画 | esm.sh |
| Babel Standalone | 7.x | JSX トランスパイル（開発時のみ） | cdnjs |

- **ビルドツール不要**（webpack / Vite 等は使用しない）
- フロントエンドは単一 HTML ファイル（`docs/index.html`）で完結

## 非機能要件（技術的制約）

| 要件 | 目標値 |
|------|-------|
| 初回ページロード（papers.json 読み込み含む） | 3 秒以内（LTE 環境） |
| フィルタ・ソート操作レスポンス | 100ms 以内（ブラウザ内処理） |
| papers.json ファイルサイズ | 圧縮後 2MB 以内（gzip） |
| ビルドパイプライン全体の実行時間 | 60 分以内（Gemini API 分類込み） |
| Gemini API 分類エラー率 | 5% 超でビルド中断してアラート |

## セキュリティ制約

- Gemini API キーはブラウザから直接呼び出し禁止（ビルド時のみ実行）
- 公開 JSON に個別レビュアーの評価スコア（個人情報）を含めない
- XSS 対策: React の JSX エスケープを利用し innerHTML 直接操作を行わない
- 外部リンク（OpenReview）には `rel="noopener noreferrer"` を付与

## 保守性・拡張性

- ビルドスクリプトは ICLR 2027 等の別年度への切り替えが設定変更のみで可能
- トピック定義（`topics.json`）は外部 JSON ファイルとして管理し、コード変更なしで更新可能

## CI/CD（オプション）

GitHub Actions による自動化（4 ジョブ構成）:
1. **fetch** — `fetch_papers.py` 実行、papers_raw.json を artifact 保存
2. **classify** — `classify_topics.py` 実行（`secrets.GEMINI_API_KEY` 参照）
3. **build** — `build_json.py` 実行し docs/ を更新
4. **deploy** — github-pages Action で docs/ をデプロイ

Trigger: main ブランチへの手動実行（`workflow_dispatch`）
