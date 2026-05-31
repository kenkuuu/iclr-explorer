"""論文リスト・ページネーションテスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_papers_container_exists(): assert 'id="papers"' in src()
def test_has_render_results(): assert "renderResults" in src()
def test_has_page_size_select(): assert "pageSizeFilter" in src()
def test_pagination_exists(): assert 'id="pager"' in src()
def test_prev_button(): assert "Prev" in src() or "prev" in src().lower()
def test_next_button(): assert "Next" in src() or "next" in src().lower()
def test_page_counter(): assert "Page" in src() and "pages" in src()
def test_shows_paper_count(): assert "fmt(rows.length)" in src() or "results" in src()
def test_paper_card_class(): assert 'class="paper"' in src()
def test_paper_title_class(): assert 'class="title"' in src()
def test_paper_authors_class(): assert 'class="authors"' in src()
def test_paper_badge_class(): assert 'class="badge' in src()
def test_paper_abstract_class(): assert 'class="abstract"' in src()
def test_et_al_authors(): assert "et al" in src()
def test_authors_sliced(): assert ".slice(0,3)" in src() or "slice(0, 3)" in src()
def test_paper_rating_displayed(): assert "rating_avg" in src()
def test_topic_chips(): assert "topic-chip" in src()
def test_openreview_link_in_card(): assert "openreview_url" in src()
def test_abstract_expandable(): s=src(); assert "open" in s and "abstract" in s
def test_title_click_toggle(): assert "classList.toggle" in src() or "toggle(" in src()
def test_mark_highlight(): assert "function mark" in src() or "<mark>" in src()
def test_paper_count_50_per_page(): s=src(); assert "50" in s and "pageSizeFilter" in s
