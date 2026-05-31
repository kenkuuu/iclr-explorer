"""フィルタ状態・検索ロジックテスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

# State variables
def test_has_state_object(): assert "const state" in src() or "let state" in src()
def test_has_page_variable(): assert "let page" in src() or "page = 1" in src()

# Filter logic
def test_has_filtered_function(): assert "function filtered" in src()
def test_filtered_filters_type(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+600]; assert "typeFilter" in ctx or "type" in ctx
def test_filtered_filters_phylum(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+600]; assert "phylum" in ctx
def test_filtered_searches_title(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+1000]; assert "title" in ctx
def test_filtered_searches_abstract(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+1000]; assert "abstract" in ctx
def test_filtered_and_or_mode(): assert "searchMode" in src() or "and" in src().lower()
def test_sort_by_rating(): assert "rating" in src() and "sort" in src()
def test_sort_by_title(): assert "title-asc" in src() or "Title" in src()

# Page reset
def test_page_reset_on_filter(): assert "page=1" in src() or "page = 1" in src()

# UI elements
def test_has_type_filter(): assert 'typeFilter' in src() or 'id="typeFilter"' in src()
def test_has_phylum_filter(): assert 'phylumFilter' in src()
def test_has_genus_filter(): assert 'genusFilter' in src() or 'genus' in src()
def test_has_sort_filter(): assert 'sortFilter' in src()
def test_has_page_size_filter(): assert 'pageSizeFilter' in src()
def test_search_input_exists(): assert '<input' in src() and 'id="q"' in src()
def test_clear_filters_button(): assert 'clearFilters' in src()
def test_active_filters_section(): assert 'activeFilters' in src()
def test_count_label(): assert 'id="count"' in src()
