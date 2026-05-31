# 要件定義書

## はじめに

ICLR 2026 Topic Explorer は、ICLR 2026 の採択論文（Poster + Oral、約 5,343 件）を OpenReview API で取得し、Gemini API でトピック自動分類した上で、インタラクティブな可視化 UI を GitHub Pages 上の静的サイトとして研究者・学生・一般閲覧者に無償公開するシステムである。

システムは「ビルドパイプライン（Python、オフライン実行）」と「静的フロントエンド（React SPA、GitHub Pages 配信）」の 2 層で構成される。

## スコープ境界

- **対象範囲**: OpenReview API によるメタデータ取得 / Gemini API によるトピック分類 / 静的 JSON 生成・GitHub Pages 配信 / React SPA による可視化 UI（トピック分布・論文一覧・論文詳細・キーワード雲・統計サマリ）
- **対象外**: 論文 PDF の取得・表示・全文検索 / ユーザー認証・個人化機能 / リアルタイム更新・WebSocket / サーバーサイドレンダリング・バックエンド API サーバ
- **隣接システム**: OpenReview（データソース）/ Gemini API（分類処理）/ GitHub Pages（ホスティング）/ GitHub Actions（CI/CD、オプション）

---

## 要件

### 要件 1: 論文メタデータ取得

**目的:** 研究者として、ICLR 2026 の全採択論文のメタデータを自動取得できるようにしたい。これにより、手動収集の手間なく最新データを利用したトピック分析が行えるようになる。

#### 受入基準

1. The Topic Explorer shall ICLR.cc/2026/Conference の採択論文（Poster + Oral）の全件（約 5,343 件）を OpenReview API v2（`https://api2.openreview.net`）から取得する。
2. When `fetch_papers.py` を実行した際、the Topic Explorer shall 各論文について `id`・`title`・`authors`・`abstract`・`keywords`・`venueid`・`decision`・`rating`（平均および詳細）フィールドを取得する。
3. The Topic Explorer shall offset / limit パラメータを用いたページネーションで全件を漏れなく取得する（limit 最大 1,000）。
4. The Topic Explorer shall リクエスト間に 0.5 秒のスリープを挿入し、OpenReview API のレート制限に準拠する。
5. When `papers_raw.json` がすでに存在する場合、the Topic Explorer shall 再取得をスキップしてキャッシュ済みデータを使用する。
6. The Topic Explorer shall 認証なし（匿名アクセス）で動作する。
7. When API レスポンスが HTTP エラーまたはタイムアウトを返した場合、the Topic Explorer shall エラーメッセージを出力して処理を中断する。

---

### 要件 2: トピック自動分類

**目的:** 研究者として、各論文のアブストラクトとキーワードから機械学習研究のトピックを自動で付与したい。これにより、5,000 件超の論文を手動でカテゴリ分けすることなく探索できるようになる。

#### 受入基準

1. The Topic Explorer shall `classify_topics.py` で論文を 50 件単位のバッチにまとめ、Gemini API（モデル: `gemini-3.5-flash`）を呼び出す。
2. The Topic Explorer shall `topics.json` に定義された 25〜35 種のカテゴリの中から各論文に `primary_topic`（1 件）および `secondary_topics`（0〜2 件）を付与する。
3. The Topic Explorer shall Gemini API のレスポンスを JSON 形式のみで受け取る（structured output、JSON Schema ネイティブ対応）。
4. If Gemini API がエラーまたはタイムアウトを返した場合、the Topic Explorer shall 最大 3 回リトライし、それでも失敗した場合は `topic=null` を付与してスキップする。
5. The Topic Explorer shall 分類済みエントリを再処理しない（checkpoint 機構により途中再開を可能にする）。
6. If 分類エラー率が 5% を超えた場合、the Topic Explorer shall ビルドを中断してアラートメッセージを出力する。
7. The Topic Explorer shall `gemini-3.5-flash` モデルのみを使用し、他モデルへのフォールバックを行わない。

---

### 要件 3: 静的 JSON 生成・配信

**目的:** 研究者として、分類済みデータがブラウザから高速に取得できる形式で配信されるようにしたい。これにより、サーバーサイド処理なしに大規模なデータセットを快適に閲覧できるようになる。

#### 受入基準

1. The Topic Explorer shall `build_json.py` で分類済みデータを `docs/data/papers.json` および `docs/data/topics.json` として出力する。
2. The Topic Explorer shall `papers.json` を gzip 圧縮後 2MB 以内に収める。
3. The Topic Explorer shall `papers.json` の `meta` フィールドに `generated_at`・`total_papers`・`model_used` を含める。
4. The Topic Explorer shall `docs/` ディレクトリを GitHub Pages の公開ルートとして使用し、CDN 経由で静的ファイルを配信する。
5. The Topic Explorer shall 個別レビュアーの評価スコア（個人情報）を配信 JSON に含めない。
6. Where GitHub Actions が設定されている場合、the Topic Explorer shall `workflow_dispatch` トリガーによる手動実行で fetch → classify → build → deploy の 4 ジョブを自動実行する。

---

### 要件 4: トピック分布可視化

**目的:** 研究者として、ICLR 2026 の採択論文がどのトピックにどれだけ集中しているかを視覚的に把握したい。これにより、研究コミュニティの注目領域を一目で理解できるようになる。

#### 受入基準

1. The Topic Explorer shall トピック別論文数を Recharts Treemap コンポーネントで可視化する。
2. The Topic Explorer shall トピック別論文数を棒グラフで表示し、クリックでそのトピックのフィルタを適用する。
3. When ユーザーが棒グラフの特定トピックをクリックした場合、the Topic Explorer shall 論文一覧をそのトピックでフィルタリングする。

---

### 要件 5: 論文一覧・フィルタリング・検索

**目的:** 研究者として、5,000 件超の論文を自分の研究テーマに応じて素早く絞り込み・検索したい。これにより、関連論文の発見にかかる時間を大幅に削減できるようになる。

#### 受入基準

1. The Topic Explorer shall トピック・採択ステータス（Oral / Poster）でフィルタリングできるようにする。
2. The Topic Explorer shall タイトルおよびアブストラクト全文のインクリメンタル検索をブラウザ内処理で実行する。
3. The Topic Explorer shall 採択スコア降順・タイトル昇順のソートを提供する。
4. The Topic Explorer shall ページネーションまたは仮想スクロールで 5,000 件を快適に表示する。
5. When フィルタ・ソート操作が行われた場合、the Topic Explorer shall 100ms 以内に結果を更新する。

---

### 要件 6: 論文詳細表示

**目的:** 研究者として、興味のある論文のアブストラクト・評価スコア・OpenReview リンクをすぐに確認したい。これにより、論文の価値を素早く判断し OpenReview へ移動できるようになる。

#### 受入基準

1. When ユーザーが論文カードをクリックした場合、the Topic Explorer shall タイトル・著者・アブストラクト・評価スコア（平均）・採択ステータス・トピックをモーダルまたは詳細パネルで表示する。
2. The Topic Explorer shall 各論文の OpenReview 論文ページへの外部リンクを提供する。
3. The Topic Explorer shall 外部リンクに `rel="noopener noreferrer"` を付与する。

---

### 要件 7: キーワード雲

**目的:** 研究者として、ICLR 2026 で頻出のキーワードをインタラクティブに探索したい。これにより、特定キーワードに関連する論文へ直接アクセスできるようになる。

#### 受入基準

1. The Topic Explorer shall `papers.json` のキーワードフィールドから頻出キーワードをタグクラウドとして表示する。
2. When ユーザーがタグクラウドのキーワードをクリックした場合、the Topic Explorer shall 論文一覧をそのキーワードで絞り込む。

---

### 要件 8: 統計サマリ

**目的:** 研究者として、ICLR 2026 の採択状況（採択率・スコア分布・ステータス内訳）を数値で把握したい。これにより、カンファレンスの全体像を定量的に理解できるようになる。

#### 受入基準

1. The Topic Explorer shall 採択率・スコア平均・Oral / Poster 比率を数値カードで表示する。
2. The Topic Explorer shall スコア分布をチャートで表示する。

---

### 要件 9: パフォーマンス要件

**目的:** 一般閲覧者として、低速な回線環境でも快適にサイトを閲覧したい。これにより、地理的・環境的な制約なくトピック探索が行えるようになる。

#### 受入基準

1. The Topic Explorer shall 初回ページロード時間（`papers.json` 読み込みを含む）を LTE 環境で 3 秒以内に完了させる。
2. The Topic Explorer shall フィルタ・ソート操作のレスポンスを 100ms 以内（ブラウザ内処理）に完了させる。
3. The Topic Explorer shall `papers.json` のファイルサイズを gzip 圧縮後 2MB 以内に収める。
4. The Topic Explorer shall ビルドパイプライン全体（Gemini API 分類込み）を 60 分以内に完了させる。

---

### 要件 10: セキュリティ・法的要件

**目的:** 開発者として、API キーの漏洩や著作権侵害のリスクなしにシステムを公開したい。これにより、安全かつ法的に問題のない形でサービスを継続できるようになる。

#### 受入基準

1. The Topic Explorer shall Gemini API キーを GitHub Actions の Secrets にのみ保存し、成果物・公開コード・ブラウザに露出させない。
2. The Topic Explorer shall Gemini API の呼び出しをビルド時のみに限定し、ブラウザからの直接呼び出しを行わない。
3. The Topic Explorer shall 論文 PDF の取得・表示を行わない（著作権は著者帰属）。
4. The Topic Explorer shall 取得するメタデータ（タイトル・著者・アブストラクト・キーワード）が OpenReview 規約により CC0 であることを確認し、サイト内に帰属表示を行う。
5. The Topic Explorer shall XSS 対策として React の JSX エスケープを利用し、innerHTML の直接操作を行わない。

---

### 要件 11: 保守性・拡張性要件

**目的:** 開発者として、毎年の ICLR 開催に合わせてシステムを最小限の変更で更新したい。これにより、将来年度への対応コストを抑えられるようになる。

#### 受入基準

1. The Topic Explorer shall ビルドスクリプトが ICLR 2027 等の別年度への切り替えを設定変更のみ（コード変更なし）で可能にする。
2. The Topic Explorer shall トピック定義を `topics.json` として外部 JSON ファイルで管理し、コード変更なしで更新・追加できるようにする。
3. The Topic Explorer shall フロントエンドを単一 HTML ファイル（`docs/index.html`）で完結させ、webpack 等のビルドツールを不要とする。
4. The Topic Explorer shall GitHub Pages の SLA（99.9%）に依存し、独自のサーバーサイドコンポーネントを持たない。
