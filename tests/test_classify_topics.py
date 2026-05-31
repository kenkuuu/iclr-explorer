"""タスク 3.1 — Gemini API 接続・Structured Output 設定の単体テスト"""
import os
from unittest import mock

import pytest
from pydantic import ValidationError

from scripts.classify_topics import (
    TopicAssignment,
    ClassificationBatch,
    create_gemini_client,
    build_classification_prompt,
    classify_batch,
    MODEL_NAME,
)


# ── Pydantic モデル検証 ────────────────────────────────────────────────────

def test_topic_assignment_valid():
    t = TopicAssignment(paper_id="p001", primary_topic="T-01", secondary_topics=[])
    assert t.paper_id == "p001"
    assert t.primary_topic == "T-01"
    assert t.secondary_topics == []


def test_topic_assignment_with_secondary():
    t = TopicAssignment(paper_id="p001", primary_topic="T-03", secondary_topics=["T-07", "T-14"])
    assert len(t.secondary_topics) == 2


def test_topic_assignment_max_two_secondary():
    with pytest.raises(ValidationError):
        TopicAssignment(
            paper_id="p001",
            primary_topic="T-01",
            secondary_topics=["T-02", "T-03", "T-04"],  # 3 件は NG
        )


def test_classification_batch_valid():
    batch = ClassificationBatch(results=[
        TopicAssignment(paper_id="p001", primary_topic="T-01", secondary_topics=[]),
        TopicAssignment(paper_id="p002", primary_topic="T-02", secondary_topics=["T-05"]),
    ])
    assert len(batch.results) == 2


def test_classification_batch_empty_results():
    batch = ClassificationBatch(results=[])
    assert batch.results == []


def test_model_name_is_gemini_flash():
    assert "gemini" in MODEL_NAME.lower()
    assert "flash" in MODEL_NAME.lower()


# ── create_gemini_client ───────────────────────────────────────────────────

def test_create_gemini_client_uses_env_key():
    with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"}):
        with mock.patch("scripts.classify_topics.genai.Client") as MockClient:
            MockClient.return_value = mock.MagicMock()
            client = create_gemini_client()
            MockClient.assert_called_once_with(api_key="test-key-123")


def test_create_gemini_client_raises_when_no_key():
    env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises((KeyError, ValueError)):
            create_gemini_client()


# ── build_classification_prompt ───────────────────────────────────────────

SAMPLE_PAPERS = [
    {
        "id": "paper001",
        "title": "Scaling Laws for LLMs",
        "abstract": "We study scaling laws for large language models...",
        "keywords": ["LLM", "scaling", "GPT"],
    },
    {
        "id": "paper002",
        "title": "Graph Neural Networks for Molecules",
        "abstract": "We propose a GNN for molecular property prediction...",
        "keywords": ["GNN", "molecules", "drug discovery"],
    },
]

SAMPLE_TOPICS = [
    {"id": "T-01", "name": "Large Language Models", "description": "LLM, GPT, instruction tuning"},
    {"id": "T-04", "name": "Graph Neural Networks", "description": "GNN, message passing, node classification"},
]


def test_prompt_includes_paper_ids():
    prompt = build_classification_prompt(SAMPLE_PAPERS, SAMPLE_TOPICS)
    assert "paper001" in prompt
    assert "paper002" in prompt


def test_prompt_includes_paper_titles():
    prompt = build_classification_prompt(SAMPLE_PAPERS, SAMPLE_TOPICS)
    assert "Scaling Laws for LLMs" in prompt
    assert "Graph Neural Networks for Molecules" in prompt


def test_prompt_includes_topic_ids():
    prompt = build_classification_prompt(SAMPLE_PAPERS, SAMPLE_TOPICS)
    assert "T-01" in prompt
    assert "T-04" in prompt


def test_prompt_includes_topic_names():
    prompt = build_classification_prompt(SAMPLE_PAPERS, SAMPLE_TOPICS)
    assert "Large Language Models" in prompt
    assert "Graph Neural Networks" in prompt


def test_prompt_is_nonempty_string():
    prompt = build_classification_prompt(SAMPLE_PAPERS, SAMPLE_TOPICS)
    assert isinstance(prompt, str)
    assert len(prompt) > 200


# ── classify_batch ─────────────────────────────────────────────────────────

def _make_mock_response(assignments: list[dict]) -> mock.MagicMock:
    """Gemini API の成功レスポンスをシミュレートする"""
    import json
    batch = {"results": assignments}
    mock_resp = mock.MagicMock()
    mock_resp.text = json.dumps(batch)
    return mock_resp


def test_classify_batch_returns_classification_batch():
    mock_client = mock.MagicMock()
    mock_client.models.generate_content.return_value = _make_mock_response([
        {"paper_id": "paper001", "primary_topic": "T-01", "secondary_topics": []},
        {"paper_id": "paper002", "primary_topic": "T-04", "secondary_topics": ["T-10"]},
    ])

    result = classify_batch(mock_client, SAMPLE_PAPERS, SAMPLE_TOPICS)

    assert isinstance(result, ClassificationBatch)
    assert len(result.results) == 2
    assert result.results[0].paper_id == "paper001"
    assert result.results[0].primary_topic == "T-01"


def test_classify_batch_calls_correct_model():
    mock_client = mock.MagicMock()
    mock_client.models.generate_content.return_value = _make_mock_response([
        {"paper_id": "paper001", "primary_topic": "T-01", "secondary_topics": []},
    ])

    classify_batch(mock_client, SAMPLE_PAPERS[:1], SAMPLE_TOPICS)

    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs.kwargs.get("model") == MODEL_NAME or \
           (call_kwargs.args and call_kwargs.args[0] == MODEL_NAME) or \
           MODEL_NAME in str(call_kwargs)


def test_classify_batch_uses_json_response_schema():
    mock_client = mock.MagicMock()
    mock_client.models.generate_content.return_value = _make_mock_response([
        {"paper_id": "paper001", "primary_topic": "T-01", "secondary_topics": []},
    ])

    classify_batch(mock_client, SAMPLE_PAPERS[:1], SAMPLE_TOPICS)

    call_kwargs = mock_client.models.generate_content.call_args
    # config に response_mime_type と response_schema が含まれること
    config_arg = call_kwargs.kwargs.get("config") or (
        call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
    )
    config_str = str(config_arg)
    assert "application/json" in config_str


def test_classify_batch_result_has_all_paper_ids():
    mock_client = mock.MagicMock()
    mock_client.models.generate_content.return_value = _make_mock_response([
        {"paper_id": "paper001", "primary_topic": "T-01", "secondary_topics": []},
        {"paper_id": "paper002", "primary_topic": "T-04", "secondary_topics": []},
    ])

    result = classify_batch(mock_client, SAMPLE_PAPERS, SAMPLE_TOPICS)
    ids = {r.paper_id for r in result.results}
    assert "paper001" in ids
    assert "paper002" in ids
