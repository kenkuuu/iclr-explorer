"""
build_json.py — 分類済み論文データから GitHub Pages 配信用 JSON を生成する

Usage:
    uv run scripts/build_json.py [--classified INPUT] [--topics TOPICS] [--output OUTPUT]
"""
import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── 定数 ─────────────────────────────────────────────────────────────────

MODEL_USED = "gemini-3.5-flash"
DEFAULT_CLASSIFIED = "data/papers_classified.json"
DEFAULT_TOPICS_IN = "data/topics.json"
DEFAULT_OUTPUT = "docs/data/papers.json"

MAX_GZIP_SIZE_BYTES = 2 * 1024 * 1024   # 2 MB
ABSTRACT_TRUNCATE_LENGTH = 500            # 文字数

# 配信 JSON に含める論文フィールド（レビュアー情報等は除外）
PAPERS_JSON_FIELDS = frozenset({
    "id",
    "title",
    "authors",
    "abstract",
    "keywords",
    "status",
    "rating_avg",
    "primary_topic",
    "secondary_topics",
    "openreview_url",
})


# ── 変換関数 ──────────────────────────────────────────────────────────────

def transform_paper(paper: dict[str, Any]) -> dict[str, Any]:
    """分類済み論文 dict → 配信スキーマ（PaperRecord）に変換する。
    PAPERS_JSON_FIELDS に含まれないフィールド（reviewer 情報等）はすべて除外する。
    topics フィールド（phylogeny multi-label）は常に含める。
    """
    result = {field: paper[field] for field in PAPERS_JSON_FIELDS if field in paper}
    # phylogeny topics を追加（存在する場合のみ）
    if "topics" in paper:
        result["topics"] = paper["topics"]
    return result


def compute_gzip_size(json_str: str) -> int:
    """JSON 文字列の gzip 圧縮後のバイト数を返す"""
    return len(gzip.compress(json_str.encode("utf-8")))


def truncate_abstracts(
    papers: list[dict[str, Any]],
    max_length: int = ABSTRACT_TRUNCATE_LENGTH,
) -> list[dict[str, Any]]:
    """全論文の abstract を max_length 文字に切り詰める（他フィールドは変更しない）"""
    result = []
    for paper in papers:
        abstract = paper.get("abstract", "")
        if len(abstract) > max_length:
            paper = {**paper, "abstract": abstract[:max_length]}
        result.append(paper)
    return result


# ── メイン生成処理 ─────────────────────────────────────────────────────────

def build_papers_json(
    classified_papers: list[dict[str, Any]],
    output_path: Path,
    model_used: str = MODEL_USED,
    generated_at: str | None = None,
) -> None:
    """
    分類済み論文リストから配信用 papers.json を生成して output_path に書き出す。

    - 個別レビュアー情報を除いた配信スキーマに変換する（セキュリティ要件 10.1）
    - gzip 後サイズが 2MB を超える場合は abstract を 500 文字に切り詰める（要件 9.3）
    - meta フィールドに generated_at・total_papers・model_used を付与する
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    papers = [transform_paper(p) for p in classified_papers]

    output = {
        "meta": {
            "generated_at": generated_at,
            "total_papers": len(papers),
            "model_used": model_used,
        },
        "papers": papers,
    }

    json_str = json.dumps(output, ensure_ascii=False)

    # gzip サイズが 2MB を超える場合は abstract を切り詰めて再生成
    if compute_gzip_size(json_str) > MAX_GZIP_SIZE_BYTES:
        print(f"[build_json] gzip サイズが 2MB を超過: abstract を {ABSTRACT_TRUNCATE_LENGTH} 文字に切り詰めます")
        papers = truncate_abstracts(papers)
        output["papers"] = papers
        json_str = json.dumps(output, ensure_ascii=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(json_str)

    final_size = compute_gzip_size(json_str)
    print(f"[build_json] papers.json 生成完了: {len(papers)} 件 / gzip {final_size / 1024:.1f} KB → {output_path}")


# ── topics.json 生成 ───────────────────────────────────────────────────────

def count_papers_by_topic(
    classified_papers: list[dict[str, Any]],
) -> dict[str, int]:
    """classified_papers の primary_topic を集計して {topic_id: count} を返す。
    primary_topic が None の論文は集計しない。
    """
    counts: dict[str, int] = {}
    for paper in classified_papers:
        topic = paper.get("primary_topic")
        if topic is not None:
            counts[topic] = counts.get(topic, 0) + 1
    return counts


def add_paper_counts(
    topic_definitions: list[dict[str, Any]],
    paper_counts: dict[str, int],
) -> list[dict[str, Any]]:
    """topic_definitions の各エントリに paper_count フィールドを追加して返す。
    counts にないトピックは 0 を設定する。元データは変更しない。
    """
    return [
        {**topic, "paper_count": paper_counts.get(topic["id"], 0)}
        for topic in topic_definitions
    ]


def build_phylogeny_json(
    phylogeny_def_path: Path,
    classified_papers: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """
    phylogeny.json の各ノードに paper_count を計算して付与し、
    docs/data/phylogeny.json として出力する。
    """
    if not phylogeny_def_path.exists():
        print(f"[build_json] Warning: {phylogeny_def_path} not found, skipping phylogeny build")
        return

    with phylogeny_def_path.open(encoding="utf-8") as f:
        tree = json.load(f)

    # genus/order/class/phylum ごとにカウント
    genus_counts:  dict[str, int] = {}
    order_counts:  dict[str, int] = {}
    class_counts:  dict[str, int] = {}
    phylum_counts: dict[str, int] = {}

    for paper in classified_papers:
        for t in paper.get("topics", []):
            genus_counts[t.get("genus","")]   = genus_counts.get(t.get("genus",""), 0) + 1
            order_counts[t.get("order","")]   = order_counts.get(t.get("order",""), 0) + 1
            class_counts[t.get("class","")]   = class_counts.get(t.get("class",""), 0) + 1
            phylum_counts[t.get("phylum","")] = phylum_counts.get(t.get("phylum",""), 0) + 1

    def annotate(node: dict, level: str) -> dict:
        name = node["name"]
        if level == "phylum":
            node["paper_count"] = phylum_counts.get(name, 0)
            node["children"] = [annotate(c, "class") for c in node.get("children", [])]
        elif level == "class":
            node["paper_count"] = class_counts.get(name, 0)
            node["children"] = [annotate(c, "order") for c in node.get("children", [])]
        elif level == "order":
            node["paper_count"] = order_counts.get(name, 0)
            node["children"] = [annotate(c, "genus") for c in node.get("children", [])]
        else:  # genus
            node["paper_count"] = genus_counts.get(name, 0)
        return node

    tree["paper_count"] = len(classified_papers)
    tree["children"] = [annotate(c, "phylum") for c in tree.get("children", [])]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"[build_json] phylogeny.json 生成完了 → {output_path}")


def build_topics_json(
    topic_definitions: list[dict[str, Any]],
    classified_papers: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """
    トピック定義と分類済み論文から docs/data/topics.json を生成する。
    各トピックに paper_count（primary_topic での集計件数）を付与する。
    """
    counts = count_papers_by_topic(classified_papers)
    topics_with_counts = add_paper_counts(topic_definitions, counts)

    output = {"topics": topics_with_counts}
    json_str = json.dumps(output, ensure_ascii=False, indent=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(json_str)

    print(f"[build_json] topics.json 生成完了: {len(topics_with_counts)} トピック → {output_path}")


# ── CLI ──────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="分類済み論文データから GitHub Pages 配信用 papers.json を生成する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  uv run scripts/build_json.py
  uv run scripts/build_json.py --classified data/papers_classified.json --output docs/data/papers.json
        """,
    )
    parser.add_argument("--classified", default=DEFAULT_CLASSIFIED,
                        help=f"分類済みデータ（デフォルト: {DEFAULT_CLASSIFIED}）")
    parser.add_argument("--topics", default=DEFAULT_TOPICS_IN,
                        help=f"トピック定義 JSON（デフォルト: {DEFAULT_TOPICS_IN}）")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"出力先（デフォルト: {DEFAULT_OUTPUT}）")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    classified_path = Path(args.classified)
    topics_path = Path(args.topics)
    output_papers = Path(args.output)
    output_topics = output_papers.parent / "topics.json"

    if not classified_path.exists():
        print(f"[build_json] エラー: {classified_path} が存在しません。先に classify_topics.py を実行してください。",
              file=sys.stderr)
        sys.exit(1)
    if not topics_path.exists():
        print(f"[build_json] エラー: {topics_path} が存在しません。", file=sys.stderr)
        sys.exit(1)

    with classified_path.open(encoding="utf-8") as f:
        classified_papers = json.load(f)
    with topics_path.open(encoding="utf-8") as f:
        topic_definitions = json.load(f)["topics"]

    print(f"[build_json] 分類済み論文: {len(classified_papers)} 件")

    print(f"[build_json] {len(classified_papers)} papers")

    # papers.json 生成（topics フィールド含む）
    build_papers_json(classified_papers, output_papers)

    # topics.json 生成（paper_count 付き）
    build_topics_json(topic_definitions, classified_papers, output_topics)

    # phylogeny.json 生成（4段階ツリー + paper_count）
    phylogeny_def_path = Path("data/phylogeny.json")
    output_phylogeny = output_papers.parent / "phylogeny.json"
    build_phylogeny_json(phylogeny_def_path, classified_papers, output_phylogeny)


if __name__ == "__main__":
    main()
