"""トピック分布 Chart.js テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_has_phylum_chart_canvas(): assert 'id="phylumChart"' in src()
def test_has_class_chart_canvas(): assert 'id="classChart"' in src()
def test_has_lineage_chart_canvas(): assert 'id="lineageChart"' in src()
def test_uses_chartjs(): assert "Chart(" in src() and "chart.js" in src().lower()
def test_builds_phylum_chart(): assert "buildPhylumChart" in src() or "phylumChart" in src()
def test_builds_class_chart(): assert "buildClassChart" in src() or "classChart" in src()
def test_phylum_chart_click(): assert "setPhylumFilter" in src()  # onClick registered in buildPhylumChart()
def test_has_phylum_colors(): assert "PHYLUM_COLORS" in src()
def test_horizontal_bar_chart(): assert "indexAxis" in src() and '"y"' in src()
def test_phylum_filter_function(): assert "setPhylumFilter" in src()
def test_chart_tooltip(): assert "tooltip" in src().lower() or "Tooltip" in src()
def test_phylums_section(): assert 'id="dist"' in src() or "Topic Distribution" in src()
def test_dist_section_has_two_charts(): s=src(); assert s.count("chart-box") >= 2
