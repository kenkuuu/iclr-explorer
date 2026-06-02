# Product Steering — ICLR 2026 Topic Explorer

## 目的

ICLR 2026 の採択論文（5,352 件、Poster + Oral）を OpenReview API で取得し、
**4 段階の Topic Phylogeny**（Phylum → Class → Order → Genus）で意味的に分類して、
インタラクティブな可視化 UI を GitHub Pages 上の静的サイトとして無償公開する。

**Live**: https://kenkuuu.github.io/iclr-explorer/

## ターゲットユーザー

| ユーザークラス | 主な利用シナリオ |
|---|---|
| ML 研究者・エンジニア | ICLR 2026 のトレンド把握、関連論文の発見 |
| 学生（大学院生） | 分野入門、研究テーマ絞り込み |
| 一般閲覧者 | AI 研究動向の概況把握 |

## 実装済み機能

| 機能 | 概要 |
|------|------|
| データ取得 | OpenReview API v2 から採択論文メタデータを取得（100% カバレッジ） |
| 4 段階 Phylogeny 分類 | Phylum→Class→Order→Genus、CVPR Explorer 参考、task/domain-first 原則 |
| ワードクラウド | アブストラクトから精選フレーズを抽出・可視化（wordcloud2.js） |
| トピック分布チャート | Phylum・Class 別の水平棒グラフ（Chart.js）、クリックでフィルタ |
| Phylogeny Tree | インタラクティブな 4 段階折りたたみツリー + 子ノードの棒グラフ |
| 論文検索 | 3 検索欄（AND/OR）、Phylum/Class/Genus ドロップダウン、タイプ別フィルタ |
| 論文カード | タイトルクリックでアブストラクト展開、OpenReview リンク |
| 統計サマリ | KPI カード（採択率・Rating 分布・Oral vs Poster ドーナツグラフ） |

## スコープ外

- 論文 PDF の取得・表示・全文検索
- ユーザー認証・個人化
- リアルタイム更新・サーバーサイド処理

## Topic Phylogeny 設計

- **10 Phylum**: Large Language Models / Multimodal & Vision-Language / Generative Models / Computer Vision / Reinforcement Learning / Embodied AI & Robotics / ML Theory & Efficient ML / Safety Robustness & Privacy / Scientific & Domain Applications / Datasets & Evaluation
- **分類原則**: Task/Domain first（方法論より問題設定・応用領域を優先）
- **Multi-label**: 1 論文に最大 3 タグ（異なる Phylum から選択）
- **100% coverage**: catch-all として "Benchmark/Dataset" と "Machine Learning" を用意

## 帰属・ライセンス

- 論文メタデータ: OpenReview CC0
- デザイン参考: CVPR 2026 Paper Explorer & CV+ML Phylogeny by gisbi-kim
- ソースコード: MIT ライセンス（GitHub: kenkuuu/iclr-explorer）
