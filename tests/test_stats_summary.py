"""統計サマリ KPI テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_kpis_section_exists(): assert 'id="kpis"' in src()
def test_builds_kpis(): assert "buildKpis" in src()
def test_shows_total_submitted(): assert "TOTAL_SUBMISSIONS" in src() and "19814" in src()
def test_shows_acceptance_rate(): assert "acceptance rate" in src().lower() or "accRate" in src()
def test_shows_oral_count(): assert "Oral" in src() and "oral" in src()
def test_shows_rating_avg(): assert "rating_avg" in src() and "avgR" in src()
def test_kpi_cards_css(): assert '.kpi' in src() or 'class="kpi' in src()
def test_kpi_has_value_element(): assert 'class="v"' in src() or '"v"' in src()
def test_kpi_total_class(): assert '"kpi total"' in src() or "kpi total" in src()
def test_top_pills(): assert "topPills" in src() or "stat-pill" in src()
def test_stat_pills_in_topbar(): assert "stat-pill" in src() and "topbar" in src()
def test_overview_section(): assert 'id="overview"' in src()
def test_phylum_count_stat(): assert "Phylums" in src() or "phylums" in src() or "Topics" in src()
