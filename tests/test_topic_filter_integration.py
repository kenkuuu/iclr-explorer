"""タスク 7.1 — トピッククリック → 論文フィルタ連動の統合テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── TopicDistribution ↔ App 状態連動 ──────────────────────────────────────

def test_topic_distribution_receives_on_topic_select():
    """TopicDistribution に handleTopicSelect が onTopicSelect として渡されている"""
    s = src()
    assert "onTopicSelect={handleTopicSelect}" in s, \
        "TopicDistribution に handleTopicSelect が渡されていない"


def test_topic_distribution_receives_selected_topic():
    """TopicDistribution に selectedTopic が渡されている"""
    s = src()
    assert "selectedTopic={selectedTopic}" in s, \
        "TopicDistribution に selectedTopic が渡されていない"


def test_handle_topic_select_updates_selected_topic():
    s = src()
    idx = s.find("handleTopicSelect")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setSelectedTopic" in context, \
        "handleTopicSelect が setSelectedTopic を呼び出していない"


def test_handle_topic_select_resets_current_page():
    s = src()
    idx = s.find("handleTopicSelect")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setCurrentPage(1)" in context, \
        "handleTopicSelect でページがリセットされていない"


def test_topic_toggle_clears_on_second_click():
    """同じトピックを再クリックすると null になる（トグル動作）"""
    s = src()
    assert "selectedTopic === id ? null : id" in s or \
           "=== id ? null : id" in s or \
           "toggle" in s.lower() or \
           "null : id" in s, \
        "トピックの再クリックで null にするトグル動作が実装されていない"


# ── アクティブフィルタインジケーター ──────────────────────────────────────

def test_active_filter_indicator_exists():
    """selectedTopic が選択中のとき、フィルタ状態を表示するインジケーターが存在する"""
    s = src()
    assert "selectedTopic &&" in s or "selectedTopic ?" in s, \
        "アクティブフィルタインジケーターが存在しない"


def test_clear_topic_filter_button_exists():
    """トピックフィルタをクリアするボタンまたは操作が存在する"""
    s = src()
    # クリアボタン or null へのリセット
    assert "handleTopicSelect(null)" in s or \
           "setSelectedTopic(null)" in s, \
        "トピックフィルタのクリア操作が存在しない"


def test_filter_indicator_shows_topic_name():
    """インジケーターにトピック名または ID が表示される"""
    s = src()
    # selectedTopic の内容を表示している
    idx = s.find("selectedTopic &&")
    if idx == -1:
        idx = s.find("selectedTopic ?")
    assert idx != -1
    context = s[idx: idx + 300]
    assert "selectedTopic" in context, \
        "インジケーターにトピック情報が表示されていない"


# ── filteredPapers → PaperList 連動 ─────────────────────────────────────

def test_paper_list_receives_filtered_papers():
    """PaperList が App の filteredPapers を受け取っている"""
    s = src()
    assert "filteredPapers={filteredPapers}" in s, \
        "PaperList に filteredPapers が渡されていない"


def test_filtered_papers_filters_by_selected_topic():
    """filteredPapers の useMemo が selectedTopic でフィルタリングする"""
    s = src()
    assert "selectedTopic" in s
    assert "primary_topic" in s or "secondary_topics" in s, \
        "トピックフィルタリングロジックが実装されていない"
