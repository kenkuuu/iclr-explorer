"""タスク 3.2 — バッチ処理ループと checkpoint 機構の単体テスト"""
import json
from pathlib import Path
from unittest import mock

import pytest

from scripts.classify_topics import (
    TopicAssignment,
    ClassificationBatch,
    classify_batch,
    load_checkpoint,
    save_checkpoint,
    run_batch_classification,
)


# ── テストデータ ──────────────────────────────────────────────────────────

def make_raw_papers(n: int, id_offset: int = 0) -> list[dict]:
    return [
        {
            "id": f"paper{i + id_offset:03d}",
            "title": f"Paper {i + id_offset}",
            "abstract": "Abstract text.",
            "authors": ["Author"],
            "keywords": ["kw"],
            "status": "Poster",
            "rating_avg": 6.0,
            "openreview_url": f"https://openreview.net/forum?id=paper{i + id_offset:03d}",
        }
        for i in range(n)
    ]


SAMPLE_TOPICS = [
    {"id": "T-01", "name": "Large Language Models", "description": "LLM"},
    {"id": "T-02", "name": "Diffusion Models", "description": "diffusion"},
]


def make_assignment(paper_id: str, topic: str = "T-01") -> TopicAssignment:
    return TopicAssignment(paper_id=paper_id, primary_topic=topic, secondary_topics=[])


def make_batch_response(paper_ids: list[str]) -> ClassificationBatch:
    return ClassificationBatch(results=[
        make_assignment(pid) for pid in paper_ids
    ])


# ── load_checkpoint ────────────────────────────────────────────────────────

def test_load_checkpoint_returns_empty_dict_when_missing(tmp_path):
    ckpt = load_checkpoint(tmp_path / "nonexistent.json")
    assert ckpt == {}


def test_load_checkpoint_returns_data_when_exists(tmp_path):
    ckpt_path = tmp_path / "checkpoint.json"
    data = {"paper001": {"paper_id": "paper001", "primary_topic": "T-01", "secondary_topics": []}}
    ckpt_path.write_text(json.dumps(data), encoding="utf-8")

    ckpt = load_checkpoint(ckpt_path)
    assert "paper001" in ckpt
    assert ckpt["paper001"]["primary_topic"] == "T-01"


def test_load_checkpoint_is_dict(tmp_path):
    ckpt_path = tmp_path / "checkpoint.json"
    ckpt_path.write_text("{}", encoding="utf-8")
    assert isinstance(load_checkpoint(ckpt_path), dict)


# ── save_checkpoint ────────────────────────────────────────────────────────

def test_save_checkpoint_creates_file(tmp_path):
    ckpt_path = tmp_path / "checkpoint.json"
    save_checkpoint({"paper001": {"primary_topic": "T-01"}}, ckpt_path)
    assert ckpt_path.exists()


def test_save_checkpoint_writes_valid_json(tmp_path):
    ckpt_path = tmp_path / "checkpoint.json"
    data = {"paper001": {"primary_topic": "T-01", "secondary_topics": []}}
    save_checkpoint(data, ckpt_path)
    loaded = json.loads(ckpt_path.read_text(encoding="utf-8"))
    assert loaded == data


def test_save_and_load_roundtrip(tmp_path):
    ckpt_path = tmp_path / "checkpoint.json"
    original = {
        "p001": {"paper_id": "p001", "primary_topic": "T-01", "secondary_topics": []},
        "p002": {"paper_id": "p002", "primary_topic": "T-03", "secondary_topics": ["T-07"]},
    }
    save_checkpoint(original, ckpt_path)
    loaded = load_checkpoint(ckpt_path)
    assert loaded == original


# ── run_batch_classification ───────────────────────────────────────────────

def make_mock_client(batches: list[list[str]]) -> mock.MagicMock:
    """指定した paper_id リストを順に返すモッククライアント"""
    client = mock.MagicMock()
    responses = []
    for batch_ids in batches:
        resp = mock.MagicMock()
        resp.text = ClassificationBatch(
            results=[make_assignment(pid) for pid in batch_ids]
        ).model_dump_json()
        responses.append(resp)
    client.models.generate_content.side_effect = responses
    return client


def test_run_batch_classification_processes_all_papers(tmp_path):
    papers = make_raw_papers(3)
    client = make_mock_client([["paper000", "paper001", "paper002"]])
    ckpt_path = tmp_path / "checkpoint.json"

    result = run_batch_classification(papers, SAMPLE_TOPICS, client,
                                      batch_size=50, checkpoint_path=ckpt_path)

    assert len(result) == 3
    assert all("primary_topic" in p for p in result)


def test_run_batch_classification_merges_raw_paper_fields(tmp_path):
    papers = make_raw_papers(1)
    client = make_mock_client([["paper000"]])
    ckpt_path = tmp_path / "checkpoint.json"

    result = run_batch_classification(papers, SAMPLE_TOPICS, client,
                                      batch_size=50, checkpoint_path=ckpt_path)

    paper = result[0]
    # RawPaper フィールドが保持されている
    assert paper["id"] == "paper000"
    assert "title" in paper
    assert "abstract" in paper
    assert "rating_avg" in paper
    # 分類結果が追加されている
    assert paper["primary_topic"] == "T-01"
    assert "secondary_topics" in paper


def test_run_batch_classification_splits_into_batches(tmp_path):
    papers = make_raw_papers(7)
    # batch_size=3 → ceil(7/3) = 3 バッチ
    client = make_mock_client([
        ["paper000", "paper001", "paper002"],
        ["paper003", "paper004", "paper005"],
        ["paper006"],
    ])
    ckpt_path = tmp_path / "checkpoint.json"

    result = run_batch_classification(papers, SAMPLE_TOPICS, client,
                                      batch_size=3, checkpoint_path=ckpt_path)

    assert client.models.generate_content.call_count == 3
    assert len(result) == 7


def test_run_batch_classification_skips_checkpointed_papers(tmp_path):
    papers = make_raw_papers(4)
    ckpt_path = tmp_path / "checkpoint.json"

    # 最初の 2 件は処理済み
    existing_ckpt = {
        "paper000": {"paper_id": "paper000", "primary_topic": "T-01", "secondary_topics": []},
        "paper001": {"paper_id": "paper001", "primary_topic": "T-02", "secondary_topics": []},
    }
    save_checkpoint(existing_ckpt, ckpt_path)

    # 残り 2 件だけ API に送られる
    client = make_mock_client([["paper002", "paper003"]])

    result = run_batch_classification(papers, SAMPLE_TOPICS, client,
                                      batch_size=50, checkpoint_path=ckpt_path)

    # API は 1 回のみ呼ばれる（残り 2 件を 1 バッチで処理）
    assert client.models.generate_content.call_count == 1
    assert len(result) == 4
    # checkpoint 済みの論文も結果に含まれる
    ids = [p["id"] for p in result]
    assert "paper000" in ids
    assert "paper001" in ids


def test_run_batch_classification_saves_checkpoint_after_each_batch(tmp_path):
    papers = make_raw_papers(4)
    ckpt_path = tmp_path / "checkpoint.json"

    client = make_mock_client([
        ["paper000", "paper001"],
        ["paper002", "paper003"],
    ])

    run_batch_classification(papers, SAMPLE_TOPICS, client,
                              batch_size=2, checkpoint_path=ckpt_path)

    # checkpoint ファイルが作成されている
    assert ckpt_path.exists()
    saved = load_checkpoint(ckpt_path)
    # 全 4 件が checkpoint に記録されている
    assert len(saved) == 4


def test_run_batch_classification_no_api_call_when_all_checkpointed(tmp_path):
    papers = make_raw_papers(2)
    ckpt_path = tmp_path / "checkpoint.json"

    # 全件処理済み
    existing_ckpt = {
        "paper000": {"paper_id": "paper000", "primary_topic": "T-01", "secondary_topics": []},
        "paper001": {"paper_id": "paper001", "primary_topic": "T-02", "secondary_topics": []},
    }
    save_checkpoint(existing_ckpt, ckpt_path)

    client = mock.MagicMock()

    run_batch_classification(papers, SAMPLE_TOPICS, client,
                              batch_size=50, checkpoint_path=ckpt_path)

    client.models.generate_content.assert_not_called()
