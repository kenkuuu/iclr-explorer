"""タスク 8.1 — ビルドパイプライン統合実行・JSON 出力の検証テスト

実際の API 呼び出しなしに、5,343 件規模のフィクスチャデータで
build_json.py のパイプライン全体を検証する。
"""
import gzip
import json
import random
from pathlib import Path

import pytest

from scripts.fetch_papers import RawPaper
from scripts.classify_topics import TopicAssignment
from scripts.build_json import (
    build_papers_json,
    build_topics_json,
    compute_gzip_size,
    MAX_GZIP_SIZE_BYTES,
    PAPERS_JSON_FIELDS,
)

ROOT = Path(__file__).parent.parent
TOPICS_PATH = ROOT / "data" / "topics.json"


# ── フィクスチャ: 5,343 件のサンプル論文 ────────────────────────────────

TOPIC_IDS = [f"T-{i:02d}" for i in range(1, 16)]
STATUSES = ["Poster", "Oral"]


def make_classified_paper(idx: int) -> dict:
    """AC-01 相当のサンプル分類済み論文を生成する"""
    return {
        "id": f"iclr2026_{idx:05d}",
        "title": f"Paper {idx}: Advances in Machine Learning Research",
        "authors": [f"Author {idx}A", f"Author {idx}B", f"Author {idx}C",
                    f"Author {idx}D"],  # 4 名（et al. テスト用）
        "abstract": (
            f"This paper presents novel approach {idx} for improving machine learning models. "
            "We demonstrate state-of-the-art results on multiple benchmarks. "
            "Our method achieves significant improvements over existing baselines. "
            "Extensive experiments validate the effectiveness of our approach. "
            "We also provide theoretical analysis and ablation studies."
        ),
        "keywords": [f"keyword{idx % 20}", f"machine learning", f"deep learning"],
        "status": STATUSES[idx % 2],
        "rating_avg": round(5.0 + (idx % 5) * 0.5, 2),
        "primary_topic": TOPIC_IDS[idx % len(TOPIC_IDS)],
        "secondary_topics": [TOPIC_IDS[(idx + 1) % len(TOPIC_IDS)]] if idx % 3 == 0 else [],
        "openreview_url": f"https://openreview.net/forum?id=iclr2026_{idx:05d}",
        # 個別レビュアー情報（出力に含めてはならない）
        "reviewer_ids": [f"~Reviewer{idx}_{j}" for j in range(3)],
        "raw_ratings": {f"~Reviewer{idx}_{j}": 6 + j for j in range(3)},
    }


@pytest.fixture(scope="module")
def classified_papers_5343():
    """5,343 件のサンプル分類済み論文リスト（AC-01 準拠）"""
    return [make_classified_paper(i) for i in range(5343)]


@pytest.fixture(scope="module")
def topic_definitions():
    """data/topics.json からトピック定義を読み込む"""
    if TOPICS_PATH.exists():
        with TOPICS_PATH.open(encoding="utf-8") as f:
            return json.load(f)["topics"]
    # topics.json が存在しない場合のフォールバック
    return [
        {"id": f"T-{i:02d}", "name": f"Topic {i}", "name_ja": f"トピック{i}",
         "description": f"Description {i}", "color": "#4FB6C6"}
        for i in range(1, 16)
    ]


# ── AC-01: papers.json 件数・primary_topic 検証 ──────────────────────────

def test_papers_json_contains_5000_plus_papers(classified_papers_5343, tmp_path):
    """AC-01: papers.json に 5,000 件以上が含まれること"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343, output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["meta"]["total_papers"] >= 5000, \
        f"papers.json の論文数が 5000 件未満: {data['meta']['total_papers']}"
    assert len(data["papers"]) >= 5000


def test_all_papers_have_primary_topic(classified_papers_5343, tmp_path):
    """AC-01: 全件に primary_topic が付与されていること"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343, output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    missing = [p["id"] for p in data["papers"] if not p.get("primary_topic")]
    assert len(missing) == 0, f"primary_topic が未付与の論文が {len(missing)} 件存在する"


# ── gzip サイズ制約 ───────────────────────────────────────────────────────

def test_papers_json_gzip_under_2mb(classified_papers_5343, tmp_path):
    """papers.json の gzip サイズが 2MB 以内であること（NFR-P-3）"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343, output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    json_text = output.read_text(encoding="utf-8")
    gz_size = compute_gzip_size(json_text)
    assert gz_size <= MAX_GZIP_SIZE_BYTES, \
        f"gzip サイズ {gz_size / 1024:.1f} KB が 2MB を超えています"


# ── セキュリティ: レビュアー情報の除外 ────────────────────────────────────

def test_papers_json_excludes_reviewer_ids(classified_papers_5343, tmp_path):
    """papers.json にレビュアー ID が含まれていないこと（NFR-S-2）"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343, output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    for paper in data["papers"]:
        assert "reviewer_ids" not in paper, "reviewer_ids がフィルタされていない"
        assert "raw_ratings" not in paper, "raw_ratings がフィルタされていない"


def test_papers_json_contains_only_allowed_fields(classified_papers_5343, tmp_path):
    """papers.json の各論文が PAPERS_JSON_FIELDS のみを含むこと"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343[:10], output,  # 10 件でチェック（高速化）
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    for paper in data["papers"]:
        extra = set(paper.keys()) - PAPERS_JSON_FIELDS
        assert not extra, f"許可されていないフィールドが含まれている: {extra}"


# ── topics.json 検証 ──────────────────────────────────────────────────────

def test_topics_json_has_paper_count(classified_papers_5343, topic_definitions, tmp_path):
    """topics.json に paper_count が付与されていること"""
    output = tmp_path / "topics.json"
    build_topics_json(topic_definitions, classified_papers_5343, output)
    data = json.loads(output.read_text(encoding="utf-8"))
    for topic in data["topics"]:
        assert "paper_count" in topic, f"paper_count がない: {topic['id']}"
        assert isinstance(topic["paper_count"], int)


def test_topics_json_paper_count_sums_to_total(classified_papers_5343, topic_definitions, tmp_path):
    """topics の paper_count 合計が論文総数と一致すること"""
    output = tmp_path / "topics.json"
    build_topics_json(topic_definitions, classified_papers_5343, output)
    data = json.loads(output.read_text(encoding="utf-8"))
    total = sum(t["paper_count"] for t in data["topics"])
    assert total == len(classified_papers_5343), \
        f"paper_count 合計 {total} が論文総数 {len(classified_papers_5343)} と一致しない"


# ── meta フィールド検証 ────────────────────────────────────────────────────

def test_papers_json_meta_has_required_fields(classified_papers_5343, tmp_path):
    """papers.json の meta に generated_at・total_papers・model_used が存在すること"""
    output = tmp_path / "papers.json"
    build_papers_json(
        classified_papers_5343, output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    meta = data["meta"]
    assert "generated_at" in meta
    assert "total_papers" in meta
    assert "model_used" in meta
    assert meta["model_used"] == "gemini-3.5-flash"
    assert meta["total_papers"] == len(classified_papers_5343)


# ── スクリプト CLI 検証 ────────────────────────────────────────────────────

def test_fetch_papers_script_has_help():
    """fetch_papers.py が --help オプションを持つ"""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fetch_papers.py"), "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "papers_raw.json" in result.stdout


def test_classify_topics_script_has_help():
    """classify_topics.py が --help オプションを持つ"""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "classify_topics.py"), "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_build_json_script_has_help():
    """build_json.py が --help オプションを持つ"""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_json.py"), "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
