# 実装タスク一覧 — ICLR 2026 Topic Explorer

## Implementation Plan

---

- [ ] 1. プロジェクト基盤セットアップ

- [x] 1.1 Python プロジェクトの初期化と依存ライブラリの設定
  - uv で pyproject.toml を作成し、`openreview-py`・`google-genai`・`pydantic`・`pandas` を依存関係に追加する
  - `GEMINI_API_KEY` を環境変数から読み込む設定方針をコメントで明記し、`.env.example` を用意する
  - `data/`・`docs/data/`・`scripts/` ディレクトリを作成し、`.gitignore` に `data/.classify_checkpoint.json` を追加する
  - `uv run scripts/fetch_papers.py --help` が実行できる状態になっていることを確認する
  - _Requirements: 10.1, 10.2, 11.1_

- [x] 1.2 トピック定義ファイル（data/topics.json）の初期作成
  - T-01〜T-15 の 15 カテゴリ（id・name・name_ja・description・color）を JSON で記述する
  - 各カテゴリに代表的なキーワード例を `description` に含め、分類プロンプトの参照材料とする
  - `paper_count` フィールドは含めない（build_json.py が計算して docs/data/ に出力する）
  - `data/topics.json` が JSON として valid であることをパースして確認できる状態になっていること
  - _Requirements: 2.2, 11.2_

- [x] 1.3 フロントエンド HTML ベースと GitHub Pages ディレクトリ構成の作成
  - `docs/index.html` に React 18・ReactDOM・Recharts・Babel Standalone の CDN import を記述する
  - `docs/data/` にサンプル `papers.json`・`topics.json`（5〜10 件分の仮データ）を配置し、ブラウザでのローカル動作確認を可能にする
  - HTML 内に OpenReview へのデータ帰属表示（クレジット文）を記述する
  - ブラウザで `docs/index.html` を開いたとき "Loading..." または仮コンポーネントが表示されることを確認する
  - _Requirements: 10.4, 11.3, 11.4_

---

- [ ] 2. 論文データ取得スクリプトの実装（fetch_papers.py）

- [x] 2.1 OpenReview API からの採択論文全件取得
  - `openreview-py` の `get_all_notes()` を用いて `ICLR.cc/2026/Conference/-/Submission` の全件を `directReplies` 付きで取得する
  - ページネーションは `get_all_notes()` が自動処理するが、リクエスト間に 0.5 秒スリープを挿入しレート制限に配慮する
  - 認証なし（匿名アクセス）で動作し、ログインなしで実行できることを確認する
  - 取得件数が標準出力に出力される状態になっていること
  - _Requirements: 1.1, 1.3, 1.4, 1.6_

- [x] 2.2 採択論文のフィルタリングとメタデータ抽出
  - `directReplies` 内の Decision ノード（invitation 末尾が `/-/Decision`）を探し、`content.decision` に "Accept" を含むものだけを採択と判定する
  - Decision 文字列から "Oral" または "Poster" を判定し `status` フィールドとして設定する（"Accept: Oral Presentation" など複数パターンに対応）
  - `directReplies` 内の Official_Review ノードから `content.rating` の数値部分を抽出し、全レビューの平均を `rating_avg` として計算する（個別レビュアー ID は保持しない）
  - PDF の URL・本文は取得せず、メタデータのみを処理することを確認する
  - 採択論文件数と Oral/Poster 内訳が標準出力に表示される状態になっていること
  - _Requirements: 1.2, 10.3_

- [x] 2.3 papers_raw.json への保存とキャッシュスキップ機構
  - 採択論文リストを `data/papers_raw.json` として JSON 保存する
  - 実行開始時に `data/papers_raw.json` が存在する場合は API 取得をスキップしてキャッシュを使用する
  - HTTP エラーまたはタイムアウト発生時はエラーメッセージを出力して処理を中断する
  - 2 回目の実行でスキップメッセージが表示され即座に終了することを確認する
  - _Requirements: 1.5, 1.7_

---

- [ ] 3. トピック分類スクリプトの実装（classify_topics.py）

- [x] 3.1 Gemini API 接続と structured output の設定
  - `google-genai` SDK で Gemini API クライアントを初期化し、環境変数から API キーを読み込む
  - 分類結果のスキーマを Pydantic モデルで定義し（`primary_topic`・`secondary_topics` フィールド）、`response_mime_type="application/json"` と `response_schema` を指定して JSON 出力を強制する
  - 50 件分の論文情報（タイトル・アブストラクト・キーワード）と利用可能なトピック定義を含むプロンプトを組み立てる
  - `gemini-3.5-flash` モデルを使用し、1 バッチ分のレスポンスが JSON として正常にパースできることを確認する
  - _Requirements: 2.1, 2.3, 2.7_

- [x] 3.2 バッチ処理ループと checkpoint 機構
  - `data/papers_raw.json` の論文を 50 件ずつバッチに分割し、順次 Gemini API を呼び出す
  - バッチ処理後に checkpoint ファイルへ処理済み論文 ID と分類結果を書き込み、中断後の再実行時はスキップする
  - 処理完了後に `data/papers_classified.json`（全論文のトピック分類結果を含む）を出力する
  - 途中で Ctrl+C して再実行した場合、未処理分のみ処理されることを確認する
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 3.3 エラーハンドリング・リトライ・エラー率監視
  - API エラー（429・5xx）は指数バックオフ（1s → 2s → 4s）＋ランダムジッターで最大 3 回リトライする
  - リトライ後も失敗した場合、および JSON パースエラーは `topic=null` としてスキップし、バッチサイズを 25 に縮小して再試行する
  - 処理が進むにつれてエラー率（`null_count / total_processed`）を計算し、5% を超えた時点でビルドを終了コード 1 で中断してアラートを出力する
  - 意図的に不正なプロンプトを渡してエラー率超過時に中断されることを確認する
  - _Requirements: 2.4, 2.6_

---

- [ ] 4. 配信 JSON 生成スクリプトの実装（build_json.py）

- [x] 4.1 papers.json の生成（スキーマ変換・セキュリティフィルタリング・サイズ確認）
  - `data/papers_classified.json` を読み込み、配信スキーマ（id・title・authors・abstract・keywords・status・rating_avg・primary_topic・secondary_topics・openreview_url）に変換する
  - 個別レビュアーの評価スコアや reviewer ID を出力に含めないことを確認する
  - `meta` フィールドに `generated_at`・`total_papers`・`model_used: "gemini-3.5-flash"` を付与する
  - 生成した JSON を gzip 圧縮して 2MB 以内に収まるかチェックし、超過した場合は `abstract` を先頭 500 文字に切り詰める
  - `docs/data/papers.json` が生成され、gzip 後のサイズが 2MB 以内であることを確認する
  - _Requirements: 3.1, 3.2, 3.3, 3.5, 9.3, 10.1_

- [x] 4.2 topics.json の生成（paper_count 計算・出力）
  - `data/topics.json`（トピック定義）を読み込み、`data/papers_classified.json` の `primary_topic` 集計から各トピックの `paper_count` を計算して追記する
  - 完成した topics データを `docs/data/topics.json` に書き出す
  - `docs/data/topics.json` が `paper_count` フィールドを含む valid な JSON として出力されることを確認する
  - _Requirements: 3.1, 3.4_

---

- [ ] 5. フロントエンド App 基盤の実装

- [x] 5.1 JSON データのフェッチとローディング・エラー状態管理
  - `docs/data/papers.json` と `docs/data/topics.json` を `Promise.all` で並行フェッチし、ローディング中はスピナーを表示する
  - フェッチ失敗時はエラーメッセージをページ全体に表示する
  - 初回ロードでデータが画面に描画されるまでの動作を仮データで確認する
  - _Requirements: 9.1_

- [x] 5.2 グローバルフィルタ状態と filteredPapers メモ化ロジック
  - `selectedTopic`・`statusFilter`・`searchQuery`（タイトル＋アブストラクト全文）・`sortBy`・`currentPage`・`selectedPaper` を App の状態として管理する
  - フィルタ条件が変化するたびに `useMemo` で `filteredPapers` を再計算し、フィルタ変更時は `currentPage` を 1 にリセットする
  - フィルタ・ソート操作後 100ms 以内に論文一覧が更新されることをブラウザで確認する
  - _Requirements: 5.1, 5.2, 5.3, 5.5, 9.2_

---

- [ ] 6. フロントエンド UI コンポーネントの実装

- [x] 6.1 (P) トピック分布コンポーネントの実装
  - topics データから Recharts Treemap を描画し、各セルにトピック名と論文数を表示する
  - topics データから Recharts 水平 BarChart（降順）を描画し、バークリックで `selectedTopic` を更新する
  - Treemap のセルまたは BarChart のバーをクリックすると論文一覧の表示が切り替わることを確認する
  - _Requirements: 4.1, 4.2, 4.3_
  - _Boundary: TopicDistribution_

- [x] 6.2 (P) 論文一覧コンポーネントの実装
  - `filteredPapers` から 1 ページあたり 100 件を表示する論文カードリストを実装する
  - 各カードにタイトル・著者（先頭 3 名＋et al.）・採択ステータス・rating_avg・primary_topic を表示する
  - 前/次ページボタンとページ番号表示によるページネーション UI を実装する
  - `React.memo` で論文カードをメモ化し、不要な再レンダリングを防止する
  - 5,000 件相当のサンプルデータでページネーションが正常に動作することを確認する
  - _Requirements: 5.4, 5.5_
  - _Boundary: PaperList_

- [x] 6.3 (P) 論文詳細モーダルの実装
  - 論文カードのクリックで `selectedPaper` を更新し、タイトル・著者全員・アブストラクト全文・rating_avg・status・トピックをモーダル表示する
  - OpenReview リンクを `rel="noopener noreferrer"` 付きで提供し、新しいタブで開く
  - モーダルを閉じると `selectedPaper` が null になり一覧に戻ることを確認する
  - _Requirements: 6.1, 6.2, 6.3_
  - _Boundary: PaperDetail_

- [x] 6.4 (P) キーワード雲コンポーネントの実装
  - `papers` 全件の `keywords` フィールドを集計し、出現頻度上位 100 件を頻度に比例したフォントサイズ（12px〜36px）でタグクラウドとして表示する
  - キーワードクリックで `searchQuery` を更新し論文一覧を絞り込む
  - キーワードをクリックすると対応する論文が一覧に表示されることを確認する
  - _Requirements: 7.1, 7.2_
  - _Boundary: KeywordCloud_

- [x] 6.5 (P) 統計サマリコンポーネントの実装
  - 総論文数・rating 平均・Oral 件数・Poster 件数を数値カードで表示する
  - rating 分布を Recharts BarChart でビン化して表示する
  - ページロード直後に統計数値が正しく描画されることを確認する
  - _Requirements: 8.1, 8.2_
  - _Boundary: StatsSummary_

---

- [ ] 7. フロントエンドコンポーネントの統合

- [x] 7.1 トピッククリックから論文一覧フィルタへの状態連動
  - TopicDistribution の `onTopicSelect` コールバックが App の `selectedTopic` を更新し、PaperList に反映されることを確認する
  - トピック選択解除（再クリックまたはクリア操作）で全件表示に戻ることを確認する
  - _Requirements: 4.3, 5.1_
  - _Depends: 6.1, 6.2_

- [x] 7.2 キーワードクリックから検索クエリへの連動と全体インタラクション検証
  - KeywordCloud の `onKeywordSelect` コールバックが `searchQuery` を更新し、PaperList がインクリメンタルに絞り込まれることを確認する
  - トピックフィルタ・ステータスフィルタ・テキスト検索・ソートを同時に組み合わせた場合も正しく動作することを確認する
  - _Requirements: 5.1, 5.2, 7.2_
  - _Depends: 6.2, 6.4_

---

- [ ] 8. 動作検証と非機能要件確認

- [x] 8.1 ビルドパイプライン統合実行と JSON 出力の検証
  - fetch → classify → build の 3 スクリプトを順番に実行し、`docs/data/papers.json` と `docs/data/topics.json` が正常に生成されることを確認する
  - `papers.json` に 5,000 件以上が含まれ、全件に `primary_topic` が付与されていることを確認する（AC-01）
  - `papers.json` の gzip サイズが 2MB 以内であること、個別レビュアー情報が含まれていないことを確認する
  - _Requirements: 3.1, 3.2, 3.3, 3.5, 9.3, 9.4_

- [x] 8.2 フロントエンド主要ユーザーフローの検証
  - 生成した実データで `docs/index.html` をブラウザで開き、初回ロードが 3 秒以内に完了することを確認する（AC-02）
  - トピックフィルタで 1 トピックを選択すると該当論文のみ表示されることを確認する（AC-03）
  - "LLM" 等のキーワード検索でタイトルまたはアブストラクトに含む論文が表示されることを確認する（AC-04）
  - 論文カードから OpenReview のリンクをクリックし論文ページへ遷移できることを確認する（AC-05）
  - モバイルブラウザの DevTools エミュレーションでレイアウト崩れがないことを確認する（AC-06）
  - _Requirements: 9.1, 9.2_

- [ ] 8.3 セキュリティ・法的要件の確認
  - `docs/data/papers.json` および `docs/data/topics.json` に `GEMINI_API_KEY` やレビュアー個人情報が含まれていないことを確認する
  - `docs/index.html` のソースに API キーが記述されていないことを確認する
  - OpenReview リンクすべてに `rel="noopener noreferrer"` が付与されていることを確認する
  - `innerHTML` の直接操作が行われていないことをコードレビューで確認する
  - _Requirements: 10.1, 10.2, 10.5_

---

- [ ]* 9. GitHub Actions ワークフロー設定（オプション）
  - fetch → classify → build → deploy の 4 ジョブを `workflow_dispatch` トリガーで実行するワークフロー YAML を作成する
  - `secrets.GEMINI_API_KEY` を classify ジョブの環境変数として参照し、コードには露出させない
  - `workflow_dispatch` で手動トリガーしたとき GitHub Pages が更新されることを確認する
  - _Requirements: 3.6, 10.1_
