# Product Steering — ICLR 2026 Topic Explorer

## 目的

ICLR 2026 の採択論文（Poster + Oral、約 5,343 件）を OpenReview API で取得し、Claude API でトピック自動分類して、インタラクティブな可視化 UI を GitHub Pages 上の静的サイトとして公開する。

## ターゲットユーザー

| ユーザークラス | 主な利用シナリオ |
|---|---|
| ML 研究者・エンジニア | トレンドトピックの調査、関連研究の発見 |
| 学生（大学院生） | 分野入門、テーマ絞り込み |
| 一般閲覧者 | AI 研究動向の概況把握 |

## 機能スコープ

### 対象機能（8 機能）

| 機能 ID | 機能名 | 概要 |
|---------|--------|------|
| F-01 | データ取得 | OpenReview API v2 で ICLR 2026 採択論文の全メタデータを取得し JSON 保存 |
| F-02 | トピック分類 | Claude API でアブストラクト＋キーワードを解析し 1〜3 トピックを付与 |
| F-03 | 静的配信 | 分類済み JSON を GitHub Pages に配置し CDN 経由で提供 |
| F-04 | トピック分布図 | トピック別論文数をツリーマップ / 棒グラフで可視化 |
| F-05 | 論文一覧 | トピック・採択ステータス・キーワードでフィルタ・ソート・検索 |
| F-06 | 論文詳細 | タイトル・アブストラクト・評価スコア・OpenReview リンクを表示 |
| F-07 | キーワード雲 | 頻出キーワードをインタラクティブなタグクラウドで表示 |
| F-08 | 統計サマリ | 採択率・スコア分布・ステータス別内訳を数値・チャートで表示 |

### スコープ外（明示的除外）

- 論文 PDF の取得・表示・全文検索
- ユーザー認証・個人化機能
- リアルタイム更新・WebSocket
- サーバーサイドレンダリング・バックエンド API サーバ

## トピックカテゴリ（暫定、約 30 種）

実データ分析後に追加・統廃合する。現在定義済みの主要カテゴリ（T-01〜T-15）:

LLM、Diffusion & Generative Models、Reinforcement Learning、Graph Neural Networks、Multimodal Learning、Federated & Privacy Learning、Efficient/Lightweight ML、Optimization & Theory、Robustness & Adversarial、Scientific Applications、Representation Learning、Computer Vision、Reasoning & Planning、Safety & Alignment、Agents & Tool Use

## ライセンス・法的制約

- メタデータ（タイトル・著者・アブストラクト・キーワード）は OpenReview 規約により CC0（配信制限なし）
- 論文 PDF 全文・本文は取得・表示しない（著作権は著者帰属）
- ソースコードは MIT ライセンスで GitHub 公開
- サイト内に OpenReview へのデータ帰属表示を行う
