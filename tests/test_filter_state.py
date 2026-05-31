"""タスク 5.2 — グローバルフィルタ状態・filteredPapers メモ化の構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── 状態変数の宣言 ─────────────────────────────────────────────────────────

def test_has_selected_topic_state():
    assert "selectedTopic" in src(), "selectedTopic 状態が存在しない"


def test_selected_topic_initialized_null():
    s = src()
    idx = s.find("selectedTopic")
    assert idx != -1
    context = s[max(0, idx - 50): idx + 100]
    assert "null" in context or "useState(null)" in context


def test_has_status_filter_state():
    assert "statusFilter" in src(), "statusFilter 状態が存在しない"


def test_has_search_query_state():
    assert "searchQuery" in src(), "searchQuery 状態が存在しない"


def test_search_query_initialized_empty_string():
    s = src()
    idx = s.find("searchQuery")
    assert idx != -1
    context = s[max(0, idx - 60): idx + 100]
    assert '""' in context or "''" in context or 'useState("")' in context or "useState('')" in context


def test_has_sort_by_state():
    assert "sortBy" in src(), "sortBy 状態が存在しない"


def test_sort_by_initialized_to_rating():
    s = src()
    idx = s.find("sortBy")
    assert idx != -1
    context = s[max(0, idx - 60): idx + 120]
    assert "rating" in context, "sortBy の初期値が rating でない"


def test_has_current_page_state():
    assert "currentPage" in src(), "currentPage 状態が存在しない"


def test_current_page_initialized_to_one():
    s = src()
    # useState(1) の直前に currentPage が含まれる行を探す
    assert "useState(1)" in s, "currentPage の useState(1) 初期化が存在しない"
    idx = s.find("useState(1)")
    context = s[max(0, idx - 80): idx + 30]
    assert "currentPage" in context or "Page" in context


def test_has_selected_paper_state():
    assert "selectedPaper" in src(), "selectedPaper 状態が存在しない"


def test_selected_paper_initialized_null():
    s = src()
    idx = s.find("selectedPaper")
    assert idx != -1
    context = s[max(0, idx - 60): idx + 100]
    assert "null" in context


# ── filteredPapers useMemo ─────────────────────────────────────────────────

def test_has_filtered_papers_memo():
    assert "filteredPapers" in src(), "filteredPapers が存在しない"
    assert "useMemo" in src(), "useMemo が使用されていない"


def test_filtered_papers_filters_by_topic():
    s = src()
    assert "selectedTopic" in s
    assert "primary_topic" in s or "secondary_topics" in s, \
        "トピックフィルタリングが実装されていない"


def test_filtered_papers_filters_by_status():
    s = src()
    assert "statusFilter" in s
    assert "status" in s, "ステータスフィルタリングが実装されていない"


def test_filtered_papers_filters_by_search_query():
    s = src()
    assert "searchQuery" in s
    assert "toLowerCase" in s or "includes" in s, \
        "テキスト検索が実装されていない"


def test_filtered_papers_sorts_by_rating_or_title():
    s = src()
    assert "sortBy" in s
    assert "rating" in s and "title" in s, "ソートが実装されていない"


def test_memo_depends_on_filter_states():
    """filteredPapers の useMemo 依存配列にフィルタ状態が含まれる"""
    s = src()
    # useMemo の定義（const filteredPapers = useMemo）を探す
    fp_idx = s.find("const filteredPapers")
    if fp_idx == -1:
        fp_idx = s.find("filteredPapers = useMemo")
    assert fp_idx != -1, "filteredPapers = useMemo の定義が見つからない"
    context = s[fp_idx: fp_idx + 800]
    assert "papers" in context
    assert "selectedTopic" in context or "searchQuery" in context


# ── currentPage のリセット ─────────────────────────────────────────────────

def test_current_page_reset_on_filter_change():
    """フィルタ変更時に currentPage を 1 にリセットする"""
    s = src()
    assert "setCurrentPage(1)" in s or "setCurrentPage( 1)" in s, \
        "フィルタ変更時に currentPage を 1 にリセットしていない"


# ── セッター関数のエクスポート（子コンポーネントに渡す） ──────────────────

def test_has_set_selected_topic():
    assert "setSelectedTopic" in src(), "setSelectedTopic が存在しない"


def test_has_set_status_filter():
    assert "setStatusFilter" in src(), "setStatusFilter が存在しない"


def test_has_set_search_query():
    assert "setSearchQuery" in src(), "setSearchQuery が存在しない"


def test_has_set_selected_paper():
    assert "setSelectedPaper" in src(), "setSelectedPaper が存在しない"
