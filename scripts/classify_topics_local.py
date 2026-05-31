"""
classify_topics_local.py — キーワードマッチングによるローカルトピック分類

外部 API 不要。data/topics.json の keywords フィールドを使い、
タイトル・キーワード・アブストラクトとの重み付きマッチングで分類する。

Usage:
    uv run scripts/classify_topics_local.py
    uv run scripts/classify_topics_local.py --input data/papers_raw.json --output data/papers_classified.json
    uv run scripts/classify_topics_local.py --stats  # 分類後の統計を表示

再分類方法:
    1. data/topics.json を編集（キーワード追加・カテゴリ分割）
    2. 上記コマンドを再実行（数秒で完了）
"""
import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any

DEFAULT_INPUT = "data/papers_raw.json"
DEFAULT_OUTPUT = "data/papers_classified.json"
DEFAULT_TOPICS = "data/topics.json"

# スコアの重み（タイトル > キーワード > アブストラクト）
TITLE_WEIGHT = 4.0
KEYWORD_WEIGHT = 2.0
ABSTRACT_WEIGHT = 1.0

# セカンダリトピックとして付与するスコア閾値（プライマリの何%以上か）
SECONDARY_THRESHOLD = 0.4

# セカンダリトピックの最大件数
MAX_SECONDARY = 2


def load_topic_keywords(topics: list[dict]) -> dict[str, list[str]]:
    """topics リストから {topic_id: [keywords...]} を構築する"""
    return {t["id"]: [kw.lower() for kw in t.get("keywords", [])] for t in topics}


def score_paper(
    title: str,
    abstract: str,
    paper_keywords: list[str],
    topic_keywords: list[str],
) -> float:
    """
    論文テキストとトピックキーワードのマッチングスコアを返す。
    タイトル・論文キーワード・アブストラクトを重み付きで評価する。
    """
    if not topic_keywords:
        return 0.0

    title_lower = title.lower()
    abstract_lower = abstract.lower()
    paper_kws_lower = " ".join(paper_keywords).lower()

    score = 0.0
    for kw in topic_keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        # タイトルマッチ（完全単語境界）
        title_hits = len(re.findall(pattern, title_lower))
        # 論文キーワードマッチ
        kw_hits = len(re.findall(pattern, paper_kws_lower))
        # アブストラクトマッチ
        abstract_hits = len(re.findall(pattern, abstract_lower))

        hit = (
            title_hits * TITLE_WEIGHT +
            kw_hits * KEYWORD_WEIGHT +
            abstract_hits * ABSTRACT_WEIGHT
        )
        if hit > 0:
            score += 1.0 + 0.3 * (hit - 1)  # 最初のヒットで 1 点、追加ヒットは 0.3 点

    return score


def classify_paper(
    paper: dict[str, Any],
    topic_keywords: dict[str, list[str]],
) -> tuple[str | None, list[str]]:
    """
    1 論文を分類し (primary_topic, secondary_topics) を返す。
    スコアが 0 の場合は primary_topic=None。
    """
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    paper_kws = paper.get("keywords", [])

    scores: dict[str, float] = {}
    for topic_id, kws in topic_keywords.items():
        scores[topic_id] = score_paper(title, abstract, paper_kws, kws)

    if not scores or max(scores.values()) == 0:
        return None, []

    # スコア降順ソート
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_id, primary_score = ranked[0]

    # セカンダリ: プライマリの SECONDARY_THRESHOLD 以上のスコアを持つもの
    secondary: list[str] = []
    for topic_id, score in ranked[1:]:
        if len(secondary) >= MAX_SECONDARY:
            break
        if score >= primary_score * SECONDARY_THRESHOLD and score > 0:
            secondary.append(topic_id)

    return primary_id, secondary


def classify_all(
    papers: list[dict[str, Any]],
    topic_keywords: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """全論文を分類して primary_topic・secondary_topics を付与する"""
    results = []
    n = len(papers)
    for i, paper in enumerate(papers):
        primary, secondary = classify_paper(paper, topic_keywords)
        classified = {
            **paper,
            "primary_topic": primary,
            "secondary_topics": secondary,
        }
        results.append(classified)
        if (i + 1) % 500 == 0 or (i + 1) == n:
            print(f"  分類済み: {i + 1:,} / {n:,} 件...", flush=True)
    return results


def print_statistics(classified: list[dict[str, Any]], topics: list[dict]) -> None:
    """分類結果の統計を表示する（カテゴリ追加・分割の参考に）"""
    topic_map = {t["id"]: t["name"] for t in topics}

    primary_counts = Counter(
        p["primary_topic"] for p in classified if p.get("primary_topic")
    )
    null_count = sum(1 for p in classified if not p.get("primary_topic"))

    print("\n" + "=" * 60)
    print("📊 分類結果統計（primary_topic）")
    print("=" * 60)
    print(f"{'カテゴリ':<45} {'件数':>6}  {'割合':>6}")
    print("-" * 60)

    total = len(classified)
    for topic_id, count in primary_counts.most_common():
        name = topic_map.get(topic_id, topic_id)
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"{topic_id} {name:<40} {count:>6}  {pct:>5.1f}%  {bar}")

    if null_count:
        pct = null_count / total * 100
        print(f"{'null（未分類）':<45} {null_count:>6}  {pct:>5.1f}%")

    print("-" * 60)
    print(f"{'合計':<45} {total:>6}")
    print()
    print("💡 件数の多いカテゴリを細分化するには:")
    print("   data/topics.json に子カテゴリを追加して再実行してください")
    print("   (parent_id / children_ids フィールドで階層を定義)")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="キーワードマッチングで論文をトピック分類する（API 不要）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  uv run scripts/classify_topics_local.py
  uv run scripts/classify_topics_local.py --stats
  uv run scripts/classify_topics_local.py --input data/papers_raw.json
        """,
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--topics", default=DEFAULT_TOPICS)
    parser.add_argument("--stats", action="store_true",
                        help="分類後に統計を表示する")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    topics_path = Path(args.topics)

    for p in [input_path, topics_path]:
        if not p.exists():
            print(f"エラー: {p} が存在しません", file=sys.stderr)
            sys.exit(1)

    with input_path.open(encoding="utf-8") as f:
        papers = json.load(f)
    with topics_path.open(encoding="utf-8") as f:
        data = json.load(f)
        topics = data["topics"]

    topic_keywords = load_topic_keywords(topics)

    print(f"[classify_local] 論文: {len(papers):,} 件 / トピック: {len(topics)} 件")
    print(f"[classify_local] キーワードマッチングで分類中...")

    classified = classify_all(papers, topic_keywords)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    classified_count = sum(1 for p in classified if p.get("primary_topic"))
    null_count = len(classified) - classified_count
    print(f"[classify_local] 完了: {classified_count:,} 件分類 / {null_count} 件未分類 → {output_path}")

    if args.stats or null_count > 0:
        print_statistics(classified, topics)


if __name__ == "__main__":
    main()
