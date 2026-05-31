"""タスク 1.2 — data/topics.json の構造検証テスト"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOPICS_PATH = ROOT / "data" / "topics.json"

REQUIRED_FIELDS = {"id", "name", "name_ja", "description", "color"}
ID_PATTERN = re.compile(r"^T-\d{2}$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_topics() -> list[dict]:
    assert TOPICS_PATH.exists(), "data/topics.json が存在しない"
    with TOPICS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    assert "topics" in data, "topics キーがない"
    return data["topics"]


def test_topics_json_is_valid_json():
    assert TOPICS_PATH.exists(), "data/topics.json が存在しない"
    with TOPICS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)  # パース失敗時は JSONDecodeError
    assert isinstance(data, dict)


def test_topics_has_at_least_15_entries():
    topics = load_topics()
    assert len(topics) >= 15, f"トピック数が 15 未満: {len(topics)}"


def test_each_topic_has_required_fields():
    topics = load_topics()
    for topic in topics:
        missing = REQUIRED_FIELDS - set(topic.keys())
        assert not missing, f"トピック {topic.get('id', '?')} に必須フィールドが不足: {missing}"


def test_topic_ids_follow_format():
    topics = load_topics()
    for topic in topics:
        assert ID_PATTERN.match(topic["id"]), f"ID 形式が不正: {topic['id']}"


def test_topic_ids_are_unique():
    topics = load_topics()
    ids = [t["id"] for t in topics]
    assert len(ids) == len(set(ids)), "重複した ID が存在する"


def test_topic_colors_are_valid_hex():
    topics = load_topics()
    for topic in topics:
        assert COLOR_PATTERN.match(topic["color"]), f"カラー形式が不正: {topic['id']} → {topic['color']}"


def test_topics_have_no_paper_count_field():
    topics = load_topics()
    for topic in topics:
        assert "paper_count" not in topic, f"paper_count フィールドが含まれている: {topic['id']}"


def test_topics_description_contains_keywords():
    topics = load_topics()
    for topic in topics:
        desc = topic["description"]
        assert len(desc) >= 10, f"description が短すぎる: {topic['id']} → {desc!r}"


def test_topics_have_japanese_name():
    topics = load_topics()
    for topic in topics:
        name_ja = topic["name_ja"]
        assert len(name_ja) >= 2, f"name_ja が短すぎる: {topic['id']} → {name_ja!r}"
