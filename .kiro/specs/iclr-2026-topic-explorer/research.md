# Research & Design Decisions

---
**Purpose**: Discovery findings and design decision rationale for ICLR 2026 Topic Explorer.

---

## Summary

- **Feature**: `iclr-2026-topic-explorer`
- **Discovery Scope**: New Feature (Greenfield) — Complex Integration（2 外部 API + 静的 SPA）
- **Key Findings**:
  - OpenReview API v2 では採択決定は `directReplies` 内の Decision ノードに格納されており、`content.decision` を直接取得できない。レーティングも同様に Review ノードを個別にパースする必要がある。
  - Gemini API の structured output は `response_mime_type="application/json"` + `response_schema` で JSON Schema ネイティブ対応（Pydantic モデルから自動変換可能）。google-genai SDK の Batch API は 50% コスト削減・通常 24 時間以内処理だが、60 分ビルド制約への適合が不確かなため同期 API を優先採用する（Batch API は将来コスト最適化候補）。
  - React 18 + Recharts 2.x の CDN SPA は技術的に実現可能だが、5,000 件の SVG 描画はボトルネックになり得る。チャート（30 トピック分）は問題なく、論文一覧はページネーションで対応する。

---

## Research Log

### OpenReview API v2 — データ構造とフィールドマッピング

- **Context**: SRS の FR-01-2 では `rating（平均・詳細）` と `decision` フィールドの取得が必要。
- **Sources**: OpenReview 公式ドキュメント（docs.openreview.net）、openreview-py v1.54.7 ソース
- **Findings**:
  - レスポンスの `content` フィールドに `title`・`abstract`・`authors`・`keywords`・`venueid` が入る。
  - 採択決定（Accept/Reject）は `details.directReplies` の中の invitation が `…/-/Decision` で終わるノードの `content.decision` フィールドに入る。
  - 採択ステータス（Oral / Poster）は同 Decision ノードの `content.decision` 値（例: "Accept: Oral Presentation"）から判定する。
  - 各レビューのレーティングは `directReplies` 内の invitation が `…/-/Official_Review` で終わるノードの `content.rating` に入る（例: "6: marginally above acceptance threshold"）。数値部分のパースが必要。
  - 個別レビュアー情報（`signatures`）は取得しても出力 JSON に含めてはならない（NFR-S-2）。
  - `openreview-py v1.54.7` の `client.get_all_notes()` が自動ページネーションを処理する。Python 3.9 以上必須。
- **Implications**:
  - `PaperFetcher` の責任に「Decision ノードからの accepted フィルタリング」「Review ノードからの rating_avg 計算」が追加される。
  - `PaperFetcher` の出力 `papers_raw.json` は accepted 論文のみを含む中間形式とする。

### Gemini API — Structured Output と同期バッチ処理

- **Context**: FR-02-3 では JSON 形式のみのレスポンスが必要、FR-02-4 でリトライが必要。
- **Sources**: google-genai SDK（最新版）、ai.google.dev/gemini-api/docs
- **Findings**:
  - **SDK**: `google-generativeai` は 2025年11月末に EOL。後継の `google-genai` が GA、本番対応済み。
  - Structured output は `response_mime_type="application/json"` + `response_schema=Model.model_json_schema()` で JSON Schema をネイティブ指定。Pydantic モデルから `.model_json_schema()` で自動変換可能。スキーマ検証は API レベルで行われるため、JSON パース失敗リスクが Claude の tool use 方式より低い。
  - **モデル選定**: `gemini-3.5-flash`（$1.50/MTok 入力・$9.00/MTok 出力）を採用。分類タスクに十分な性能、コスト試算 ~$0.5〜1 USD（Claude 比 1/5〜1/8）。`gemini-3.1-flash-lite`（$0.25/MTok）は低コストだが分類精度の評価が必要。
  - **Batch API**: `client.batches.create()` で 50% 割引・最大 24 時間処理。60 分制約への適合が不確かなため同期 API を優先。将来のコスト最適化候補として記録。
  - **API キー**: 環境変数 `GEMINI_API_KEY`（`GOOGLE_API_KEY` も可だが競合リスクあり。`GEMINI_API_KEY` を明示推奨）。
  - レート制限（有料 Tier 1）: 2,000 RPM、4M TPM。50 件バッチ・110 リクエスト程度は問題なし。
- **Implications**:
  - `TopicClassifier` の SDK を `anthropic` から `google-genai` に変更。
  - `max_tokens` 制限による切り詰めリスクが構造的に低減される（スキーマ強制のため）。パース失敗は依然として起こり得るのでバリデーションは維持する。
  - JSON パース失敗検出時はバッチサイズを 25 に縮小して再試行する。

### React 18 + Recharts CDN SPA — パフォーマンスと制約

- **Context**: NFR-M-3 でビルドツール不要・単一 HTML。FR-05-4 で 5,000 件表示。
- **Sources**: esm.sh ドキュメント、Recharts 公式、GitHub Pages CORS ドキュメント
- **Findings**:
  - React 18.3.1: `https://esm.sh/react@18.3.1` / ReactDOM: `https://esm.sh/react-dom@18.3.1/client`
  - Recharts 2.x: `https://esm.sh/recharts` (esm.sh 経由は非公式だが動作確認済み)
  - Babel Standalone 7.x: `https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.28.4/babel.min.js`
  - Recharts は SVG ベース。30 トピックのチャートは問題なし。
  - 5,000 件すべてを仮想スクロールで表示するには専用ライブラリ（react-virtual 等）が必要で、CDN のみ構成が複雑になる。ページネーション（100 件/ページ）が現実的。
  - GitHub Pages は `Access-Control-Allow-Origin: *` を付与しており、`fetch()` で同一リポジトリ内の JSON 取得は問題なし。
- **Implications**:
  - 論文一覧は仮想スクロールではなくページネーションを採用する（FR-05-4 対応）。
  - `React.memo` + `useMemo` によるフィルタ結果のメモ化でフィルタ操作 100ms 以内を達成する。

---

## Architecture Pattern Evaluation

| オプション | 説明 | 長所 | リスク / 制限 | 採否 |
|-----------|------|------|-------------|------|
| 2 層（パイプライン + 静的 SPA） | ビルド時 Python → 静的 JSON → React SPA | サーバー不要、運用コスト ゼロ、スケール無限 | ビルド毎に再分類が必要、リアルタイム更新不可 | **採用** |
| SSR（Next.js 等） | サーバーサイドでレンダリング | リアルタイム性が高い | GitHub Pages で動作不可、スコープ外 | 不採用 |
| バックエンド API サーバ | Express 等でデータを API 提供 | 動的フィルタリング可 | 運用コスト発生、スコープ外 | 不採用 |
| Gemini Batch API | 非同期バッチで 50% コスト削減 | コスト安（~$0.25〜0.5 USD）| 24 時間以内処理、60 分制約への適合不確か | 不採用（将来検討）|

---

## Design Decisions

### Decision: OpenReview フィルタリング戦略

- **Context**: accepted 論文の判定が直接フィールドにない（directReplies に埋め込み）
- **Alternatives Considered**:
  1. venueid によるフィルタリング — venueid が "ICLR.cc/2026/Conference" を含む場合を採択と判定
  2. directReplies の Decision ノードを解析 — `content.decision` に "Accept" を含む場合を採択と判定
- **Selected Approach**: 2（directReplies 解析）。Decision ノードから Oral/Poster の判定も同時に行う。
- **Rationale**: venueid は会議によって構造が異なる。Decision ノードの解析がより堅牢。
- **Trade-offs**: 処理が複雑になるが、Oral/Poster 判定が同時に取得できる。
- **Follow-up**: ICLR 2026 の actual decision 文字列パターン（"Accept: Oral Presentation" 等）を実データで確認。

### Decision: ページネーション vs 仮想スクロール

- **Context**: FR-05-4 で 5,000 件を快適に表示する必要がある
- **Alternatives Considered**:
  1. 仮想スクロール — `react-window` 等、CDN 経由で追加ライブラリが必要
  2. ページネーション — 標準 JS で実装可能、追加ライブラリ不要
- **Selected Approach**: ページネーション（100 件/ページ）
- **Rationale**: CDN のみ構成（ビルドツール不要）に合致。react-window の esm.sh 互換性が不確実。
- **Trade-offs**: スクロール体験は仮想スクロールに劣るが、実装が確実でメンテナンスが容易。

### Decision: Checkpoint 機構の実装

- **Context**: FR-02-6 で中断後の再開が可能である必要がある
- **Alternatives Considered**:
  1. 処理済み paper_id を Set として checkpoint JSON に保存
  2. papers_classified.json に逐次追記
- **Selected Approach**: 1（checkpoint JSON で管理）+ 2（分類完了後に出力）
- **Rationale**: checkpoint ファイルを分離することで、papers_classified.json の整合性を保つ。
- **Trade-offs**: ファイルが 2 つになるが、再実行時の安全性が高い。

---

## Risks & Mitigations

- **ICLR 2026 の Decision 文字列が異なる形式** — `fetch_papers.py` で複数パターン（"Accept: Oral"・"Accept: Poster"・"Accept"）を対応済みとしてドキュメント化。実データ確認後に調整。
- **Gemini API の JSON パース失敗** — スキーマ強制により Claude 比でリスクは低いが、パース失敗検出時はバッチサイズを 25 に縮小して再試行。
- **Recharts の esm.sh 非公式サポート** — `jsdelivr.com/package/npm/recharts` の UMD ビルドを代替として使用可能。
- **papers.json のサイズ超過（2MB 制限）** — `abstract` フィールドを先頭 500 文字に切り詰める圧縮オプションを build_json.py に実装。

---

## References

- [OpenReview API V2 リファレンス](https://docs.openreview.net/reference/api-v2)
- [openreview-py ドキュメント](https://openreview-py.readthedocs.io/en/latest/)
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)
- [Gemini API Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [esm.sh CDN](https://esm.sh/)
- [Recharts パフォーマンスガイド](https://recharts.github.io/en-US/guide/performance/)
- [GitHub Pages CORS サポート](https://docs.github.com/en/rest/using-the-rest-api/using-cors-and-jsonp-to-make-cross-origin-requests)
