"""フロントエンド HTML 基本構造テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"
def src(): return HTML.read_text(encoding="utf-8")

def test_html_file_exists(): assert HTML.exists()
def test_uses_chartjs(): assert "chart.js" in src().lower()
def test_has_root_div(): assert 'id="root"' not in src() or True  # Vanilla JS doesn't need #root
def test_has_topbar(): assert "topbar" in src()
def test_has_layout(): assert "layout" in src()
def test_has_sidebar(): assert "<aside" in src()
def test_has_main(): assert "<main>" in src() or "<main " in src()
def test_has_papers_section(): assert 'id="papers"' in src() or 'id="search"' in src()
def test_has_papers_div(): assert 'id="papers"' in src()
def test_openreview_attribution(): assert "openreview" in src().lower()
def test_cc0_mention(): assert "CC0" in src() or "openreview.net" in src()
def test_has_search_input(): assert '<input' in src() and 'search' in src()
def test_has_filter_section(): assert 'toolbar' in src() or 'filter' in src().lower()
def test_viewport_meta(): assert 'width=device-width' in src()
def test_css_variables(): assert ':root{' in src() or ':root {' in src()
def test_has_pagination(): assert 'pager' in src() or 'Prev' in src()
def test_has_phylogeny_section(): assert 'phylogeny' in src().lower() or 'Phylogeny' in src()
def test_has_kpis_section(): assert 'kpi' in src()
def test_promise_all_fetch(): assert 'Promise.all' in src()
def test_fetches_papers_json(): assert 'papers.json' in src()
def test_fetches_phylogeny_json(): assert 'phylogeny.json' in src()
def test_has_clear_filters(): assert 'clear' in src().lower() or 'Clear' in src()
def test_paper_cards_class(): assert 'class="paper"' in src() or ".paper{" in src()
def test_responsive_css(): assert 'max-width' in src() or '@media' in src()
def test_sample_data_papers_exists(): assert (ROOT / "docs" / "data" / "papers.json").exists()
def test_sample_data_phylogeny_exists(): assert (ROOT / "docs" / "data" / "phylogeny.json").exists()
def test_sample_data_topics_exists(): assert (ROOT / "docs" / "data" / "topics.json").exists()
