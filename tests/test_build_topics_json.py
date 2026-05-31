"""タスク 4.2 — topics.json 生成（paper_count 計算・出力）の単体テスト"""
import json
from pathlib import Path

import pytest

from scripts.build_json import (
    count_papers_by_topic,
    add_paper_counts,
    build_topics_json,
)

# ── テストデータ ──────────────────────────────────────────────────────────

TOPIC_DEFS = [
    {"id": "T-01", "name": "LLM", "name_ja": "大規模言語モデル",
     "description": "LLM, GPT", "color": "#4FB6C6"},
    {"id": "T-02", "name": "Diffusion", "name_ja": "拡散モデル",
     "description": "diffusion, DDPM", "color": "#E07B54"},
    {"id": "T-03", "name": "RL", "name_ja": "強化学習",
     "description": "RL, policy gradient", "color": "#7B5EA7"},
]

def make_classified(primary_topics: list[str | None]) -> list[dict]:
    return [
        {"id": f"paper{i:03d}", "title": "T", "primary_topic": pt,
         "secondary_topics": [], "status": "Poster", "rating_avg": 6.0,
         "abstract": "A", "authors": [], "keywords": [],
         "openreview_url": "https://openreview.net/forum?id=x"}
        for i, pt in enumerate(primary_topics)
    ]


# ── count_papers_by_topic ─────────────────────────────────────────────────

def test_count_papers_by_topic_basic():
    papers = make_classified(["T-01", "T-01", "T-02"])
    counts = count_papers_by_topic(papers)
    assert counts["T-01"] == 2
    assert counts["T-02"] == 1


def test_count_papers_by_topic_missing_topics_have_zero():
    papers = make_classified(["T-01"])
    counts = count_papers_by_topic(papers)
    assert counts.get("T-03", 0) == 0


def test_count_papers_by_topic_ignores_null_primary_topic():
    papers = make_classified([None, "T-01", None])
    counts = count_papers_by_topic(papers)
    assert counts.get("T-01") == 1
    # None は集計されない
    assert None not in counts


def test_count_papers_by_topic_empty_papers():
    counts = count_papers_by_topic([])
    assert counts == {}


def test_count_papers_by_topic_returns_dict():
    counts = count_papers_by_topic(make_classified(["T-01"]))
    assert isinstance(counts, dict)


# ── add_paper_counts ───────────────────────────────────────────────────────

def test_add_paper_counts_adds_field():
    counts = {"T-01": 5, "T-02": 3}
    result = add_paper_counts(TOPIC_DEFS, counts)
    t01 = next(t for t in result if t["id"] == "T-01")
    assert t01["paper_count"] == 5


def test_add_paper_counts_zero_for_missing_topics():
    counts = {"T-01": 10}  # T-02・T-03 の counts なし
    result = add_paper_counts(TOPIC_DEFS, counts)
    t02 = next(t for t in result if t["id"] == "T-02")
    assert t02["paper_count"] == 0


def test_add_paper_counts_preserves_original_fields():
    counts = {"T-01": 2}
    result = add_paper_counts(TOPIC_DEFS, counts)
    t01 = next(t for t in result if t["id"] == "T-01")
    assert t01["name"] == "LLM"
    assert t01["name_ja"] == "大規模言語モデル"
    assert t01["description"] == "LLM, GPT"
    assert t01["color"] == "#4FB6C6"


def test_add_paper_counts_does_not_modify_input():
    counts = {"T-01": 5}
    original_topic = dict(TOPIC_DEFS[0])  # コピー
    add_paper_counts(TOPIC_DEFS, counts)
    assert TOPIC_DEFS[0] == original_topic  # 元データが変わっていない


def test_add_paper_counts_returns_all_topics():
    counts = {"T-01": 100}
    result = add_paper_counts(TOPIC_DEFS, counts)
    assert len(result) == len(TOPIC_DEFS)


# ── build_topics_json ──────────────────────────────────────────────────────

def test_build_topics_json_creates_file(tmp_path):
    output = tmp_path / "topics.json"
    papers = make_classified(["T-01", "T-01", "T-02"])
    build_topics_json(TOPIC_DEFS, papers, output)
    assert output.exists()


def test_build_topics_json_output_is_valid_json(tmp_path):
    output = tmp_path / "topics.json"
    papers = make_classified(["T-01"])
    build_topics_json(TOPIC_DEFS, papers, output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_build_topics_json_has_topics_key(tmp_path):
    output = tmp_path / "topics.json"
    papers = make_classified(["T-01"])
    build_topics_json(TOPIC_DEFS, papers, output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "topics" in data
    assert isinstance(data["topics"], list)


def test_build_topics_json_correct_paper_count(tmp_path):
    output = tmp_path / "topics.json"
    papers = make_classified(["T-01", "T-01", "T-01", "T-02"])
    build_topics_json(TOPIC_DEFS, papers, output)
    data = json.loads(output.read_text(encoding="utf-8"))

    t01 = next(t for t in data["topics"] if t["id"] == "T-01")
    t02 = next(t for t in data["topics"] if t["id"] == "T-02")
    t03 = next(t for t in data["topics"] if t["id"] == "T-03")

    assert t01["paper_count"] == 3
    assert t02["paper_count"] == 1
    assert t03["paper_count"] == 0


def test_build_topics_json_preserves_all_topic_fields(tmp_path):
    output = tmp_path / "topics.json"
    build_topics_json(TOPIC_DEFS, make_classified(["T-01"]), output)
    data = json.loads(output.read_text(encoding="utf-8"))

    t01 = next(t for t in data["topics"] if t["id"] == "T-01")
    assert "id" in t01
    assert "name" in t01
    assert "name_ja" in t01
    assert "description" in t01
    assert "color" in t01
    assert "paper_count" in t01


def test_build_topics_json_all_topics_have_paper_count(tmp_path):
    output = tmp_path / "topics.json"
    build_topics_json(TOPIC_DEFS, make_classified([]), output)  # 論文なし
    data = json.loads(output.read_text(encoding="utf-8"))
    for topic in data["topics"]:
        assert "paper_count" in topic
        assert isinstance(topic["paper_count"], int)


def test_build_topics_json_creates_parent_dirs(tmp_path):
    output = tmp_path / "nested" / "deep" / "topics.json"
    build_topics_json(TOPIC_DEFS, make_classified(["T-01"]), output)
    assert output.exists()
