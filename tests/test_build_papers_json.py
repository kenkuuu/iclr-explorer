"""タスク 4.1 — papers.json 生成（スキーマ変換・セキュリティ・サイズ確認）の単体テスト"""
import gzip
import json
from pathlib import Path

import pytest

from scripts.build_json import (
    transform_paper,
    compute_gzip_size,
    truncate_abstracts,
    build_papers_json,
    PAPERS_JSON_FIELDS,
    MAX_GZIP_SIZE_BYTES,
    ABSTRACT_TRUNCATE_LENGTH,
    MODEL_USED,
)

# ── テスト用サンプルデータ ─────────────────────────────────────────────────

SAMPLE_CLASSIFIED = {
    "id": "paper001",
    "title": "A Great Paper",
    "authors": ["Alice", "Bob"],
    "abstract": "This paper introduces a novel approach...",
    "keywords": ["LLM", "scaling"],
    "status": "Oral",
    "rating_avg": 8.0,
    "primary_topic": "T-01",
    "secondary_topics": ["T-08"],
    "openreview_url": "https://openreview.net/forum?id=paper001",
}

# 個別レビュアー情報（出力に含めてはならない）
SAMPLE_WITH_SENSITIVE = {
    **SAMPLE_CLASSIFIED,
    "reviewer_ids": ["~Reviewer1", "~Reviewer2"],
    "raw_ratings": {"~Reviewer1": 8, "~Reviewer2": 9},
    "extra_internal_field": "should_be_excluded",
}


def make_papers(n: int, abstract_len: int = 100) -> list[dict]:
    return [
        {**SAMPLE_CLASSIFIED,
         "id": f"paper{i:04d}",
         "abstract": "A" * abstract_len,
         "openreview_url": f"https://openreview.net/forum?id=paper{i:04d}"}
        for i in range(n)
    ]


# ── PAPERS_JSON_FIELDS ──────────────────────────────────────────────────────

def test_papers_json_fields_includes_required():
    required = {"id", "title", "authors", "abstract", "keywords",
                "status", "rating_avg", "primary_topic", "secondary_topics", "openreview_url"}
    assert required.issubset(PAPERS_JSON_FIELDS)


# ── transform_paper ────────────────────────────────────────────────────────

def test_transform_paper_includes_all_required_fields():
    result = transform_paper(SAMPLE_CLASSIFIED)
    for field in PAPERS_JSON_FIELDS:
        assert field in result, f"フィールド {field!r} が変換結果に含まれていない"


def test_transform_paper_excludes_sensitive_fields():
    result = transform_paper(SAMPLE_WITH_SENSITIVE)
    assert "reviewer_ids" not in result
    assert "raw_ratings" not in result
    assert "extra_internal_field" not in result


def test_transform_paper_preserves_values():
    result = transform_paper(SAMPLE_CLASSIFIED)
    assert result["id"] == "paper001"
    assert result["title"] == "A Great Paper"
    assert result["authors"] == ["Alice", "Bob"]
    assert result["status"] == "Oral"
    assert result["rating_avg"] == 8.0
    assert result["primary_topic"] == "T-01"


def test_transform_paper_no_pdf_url():
    result = transform_paper(SAMPLE_CLASSIFIED)
    assert "pdf" not in result


# ── compute_gzip_size ──────────────────────────────────────────────────────

def test_compute_gzip_size_returns_int():
    size = compute_gzip_size('{"hello": "world"}')
    assert isinstance(size, int)
    assert size > 0


def test_compute_gzip_size_larger_for_longer_text():
    small = compute_gzip_size("short")
    large = compute_gzip_size("A" * 10000)
    assert large > small


def test_max_gzip_size_is_2mb():
    assert MAX_GZIP_SIZE_BYTES == 2 * 1024 * 1024


# ── truncate_abstracts ─────────────────────────────────────────────────────

def test_truncate_abstracts_short_abstracts_unchanged():
    papers = [{"abstract": "Short abstract."}]
    result = truncate_abstracts(papers)
    assert result[0]["abstract"] == "Short abstract."


def test_truncate_abstracts_long_abstracts_cut():
    long_abstract = "A" * 600
    papers = [{"abstract": long_abstract}]
    result = truncate_abstracts(papers)
    assert len(result[0]["abstract"]) == ABSTRACT_TRUNCATE_LENGTH


def test_truncate_abstracts_does_not_modify_other_fields():
    papers = [{"id": "p001", "title": "T", "abstract": "A" * 600}]
    result = truncate_abstracts(papers)
    assert result[0]["id"] == "p001"
    assert result[0]["title"] == "T"


def test_truncate_abstracts_preserves_all_papers():
    papers = [{"abstract": "x" * 600} for _ in range(5)]
    result = truncate_abstracts(papers)
    assert len(result) == 5


def test_abstract_truncate_length_is_500():
    assert ABSTRACT_TRUNCATE_LENGTH == 500


# ── build_papers_json ─────────────────────────────────────────────────────

def test_build_papers_json_creates_file(tmp_path):
    output = tmp_path / "papers.json"
    build_papers_json(
        [SAMPLE_CLASSIFIED], output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    assert output.exists()


def test_build_papers_json_has_meta_field(tmp_path):
    output = tmp_path / "papers.json"
    build_papers_json(
        [SAMPLE_CLASSIFIED], output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "meta" in data
    assert data["meta"]["total_papers"] == 1
    assert data["meta"]["model_used"] == MODEL_USED
    assert data["meta"]["generated_at"] == "2026-05-30T00:00:00+00:00"


def test_build_papers_json_has_papers_field(tmp_path):
    output = tmp_path / "papers.json"
    build_papers_json(
        make_papers(3), output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "papers" in data
    assert len(data["papers"]) == 3


def test_build_papers_json_output_is_valid_json(tmp_path):
    output = tmp_path / "papers.json"
    build_papers_json(
        make_papers(5), output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_build_papers_json_excludes_sensitive_fields(tmp_path):
    output = tmp_path / "papers.json"
    build_papers_json(
        [SAMPLE_WITH_SENSITIVE], output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    paper = data["papers"][0]
    assert "reviewer_ids" not in paper
    assert "raw_ratings" not in paper


def test_build_papers_json_truncates_abstract_when_oversized(tmp_path):
    """gzip サイズが 2MB を超えた場合に abstract を 500 文字に切り詰める"""
    from unittest import mock

    output = tmp_path / "papers.json"
    papers = make_papers(5, abstract_len=1000)

    # 1 回目の gzip チェック: 2MB 超と偽装 → truncate が実行される
    # 2 回目（最終サイズ表示）: 正常値を返す
    with mock.patch("scripts.build_json.compute_gzip_size",
                    side_effect=[MAX_GZIP_SIZE_BYTES + 1, MAX_GZIP_SIZE_BYTES - 1]):
        build_papers_json(papers, output, generated_at="2026-05-30T00:00:00+00:00")

    data = json.loads(output.read_text(encoding="utf-8"))
    for paper in data["papers"]:
        assert len(paper["abstract"]) <= ABSTRACT_TRUNCATE_LENGTH


def test_build_papers_json_output_gzip_under_2mb(tmp_path):
    """出力 JSON の gzip サイズが 2MB 以内であること"""
    output = tmp_path / "papers.json"
    papers = make_papers(1000, abstract_len=3000)

    build_papers_json(papers, output, generated_at="2026-05-30T00:00:00+00:00")

    json_text = output.read_text(encoding="utf-8")
    gzip_size = compute_gzip_size(json_text)
    assert gzip_size <= MAX_GZIP_SIZE_BYTES, (
        f"gzip サイズ {gzip_size / 1024:.1f} KB が 2MB を超えています"
    )


def test_build_papers_json_creates_parent_dirs(tmp_path):
    output = tmp_path / "nested" / "deep" / "papers.json"
    build_papers_json(
        [SAMPLE_CLASSIFIED], output,
        generated_at="2026-05-30T00:00:00+00:00"
    )
    assert output.exists()


def test_model_used_constant_is_gemini():
    assert "gemini" in MODEL_USED.lower()
