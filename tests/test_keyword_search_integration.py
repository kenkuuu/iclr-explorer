"""キーワード検索・複合フィルタ統合テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_search_q1(): assert 'id="q"' in src()
def test_search_q2(): assert 'id="q2"' in src()
def test_search_q3(): assert 'id="q3"' in src()
def test_and_or_mode(): assert 'id="searchMode"' in src()
def test_and_option(): assert '<option value="and">' in src() or "and" in src()
def test_or_option(): assert '<option value="or">' in src() or '"or"' in src()
def test_search_filters_title(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+800]; assert "title" in ctx
def test_search_filters_abstract(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+800]; assert "abstract" in ctx
def test_type_filter_exists(): assert 'id="typeFilter"' in src()
def test_phylum_filter_exists(): assert 'id="phylumFilter"' in src()
def test_class_filter_exists(): assert 'id="classFilter"' in src()
def test_genus_filter_exists(): assert 'id="genusFilter"' in src()
def test_sort_filter_exists(): assert 'id="sortFilter"' in src()
def test_page_size_filter(): assert 'id="pageSizeFilter"' in src()
def test_clear_filters_button(): assert 'id="clearFilters"' in src()
def test_mark_highlights_search(): assert "function mark" in src()
def test_filtered_depends_on_mode(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+800]; assert "mode" in ctx or "searchMode" in ctx
def test_has_topic_chips_filter(): assert "topic-chip" in src() and "phylum" in src()
def test_combined_filters_apply(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+800]; assert "phylum" in ctx and "type" in ctx
def test_active_filters_shown(): assert "activeFilters" in src() and "filter-chip" in src()
