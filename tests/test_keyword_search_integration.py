"""タスク 7.2 — キーワード検索連動・全体インタラクション確認の統合テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── KeywordCloud → searchQuery 連動 ───────────────────────────────────────

def test_keyword_cloud_connected_to_handle_search():
    """KeywordCloud の onKeywordSelect に handleSearch が渡されている"""
    s = src()
    assert "onKeywordSelect={handleSearch}" in s, \
        "KeywordCloud に handleSearch が onKeywordSelect として渡されていない"


def test_handle_search_updates_search_query():
    """handleSearch が setSearchQuery を呼び出す"""
    s = src()
    idx = s.find("handleSearch")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setSearchQuery" in context, \
        "handleSearch が setSearchQuery を呼び出していない"


def test_handle_search_resets_current_page():
    """handleSearch でページがリセットされる"""
    s = src()
    idx = s.find("handleSearch")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setCurrentPage(1)" in context, \
        "handleSearch でページがリセットされていない"


# ── テキスト検索入力フィールド ────────────────────────────────────────────

def test_search_input_field_exists():
    """テキスト検索入力フィールドが存在する"""
    s = src()
    assert '<input' in s or "type=\"search\"" in s or "type=\"text\"" in s or \
           "searchQuery" in s and "onChange" in s, \
        "テキスト検索入力フィールドが存在しない"


def test_search_input_connected_to_search_query():
    """検索フィールドが searchQuery 状態と連動している"""
    s = src()
    assert "handleSearch" in s and "onChange" in s, \
        "検索フィールドが handleSearch に接続されていない"


# ── ステータスフィルタ UI ─────────────────────────────────────────────────

def test_status_filter_buttons_exist():
    """Oral/Poster ステータスフィルタが存在する"""
    s = src()
    has_oral_button = "Oral" in s and "handleStatusFilter" in s
    has_status_control = "statusFilter" in s and ("Oral" in s or "status" in s)
    assert has_oral_button or has_status_control, \
        "ステータスフィルタ UI が存在しない"


def test_handle_status_filter_updates_state():
    """handleStatusFilter が setStatusFilter を呼び出す"""
    s = src()
    idx = s.find("handleStatusFilter")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setStatusFilter" in context, \
        "handleStatusFilter が setStatusFilter を呼び出していない"


# ── ソート UI ──────────────────────────────────────────────────────────────

def test_sort_control_exists():
    """ソートコントロールが存在する"""
    s = src()
    assert "handleSortChange" in s, "ソートコントロールが存在しない"
    assert "rating" in s and ("title" in s or "Title" in s), \
        "ソートオプション（rating / title）が存在しない"


def test_handle_sort_change_updates_state():
    """handleSortChange が setSortBy を呼び出す"""
    s = src()
    idx = s.find("handleSortChange")
    assert idx != -1
    context = s[idx: idx + 150]
    assert "setSortBy" in context, \
        "handleSortChange が setSortBy を呼び出していない"


# ── 複合フィルタの useMemo 依存配列 ──────────────────────────────────────

def test_filtered_papers_depends_on_all_filters():
    """filteredPapers の useMemo が全フィルタ状態に依存している"""
    s = src()
    fp_idx = s.find("const filteredPapers")
    if fp_idx == -1:
        fp_idx = s.find("filteredPapers = useMemo")
    assert fp_idx != -1

    # 依存配列（useMemo の第 2 引数）を探す
    context = s[fp_idx: fp_idx + 1200]
    assert "papers" in context
    assert "selectedTopic" in context
    assert "statusFilter" in context
    assert "searchQuery" in context
    assert "sortBy" in context


def test_text_search_filters_title_and_abstract():
    """テキスト検索がタイトルとアブストラクト両方に適用される"""
    s = src()
    assert "title" in s and "abstract" in s and "toLowerCase" in s, \
        "テキスト検索がタイトルとアブストラクトに適用されていない"
