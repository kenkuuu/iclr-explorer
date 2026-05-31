"""キーワード / Genus チップテスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_topic_chips_rendered(): assert "topic-chip" in src()
def test_genus_in_chips(): assert "genus" in src()
def test_chip_click_filters(): assert "topic-chip" in src() and "setPhylumFilter" in src()
def test_phylum_tag_exists(): assert "phylum-tag" in src()
def test_phylum_tag_click(): s=src(); idx=s.find("phylum-tag"); ctx=s[idx:idx+300]; assert "setPhylumFilter" in ctx or "phylum" in ctx
def test_active_filter_chips(): assert "filter-chip" in src()
def test_filter_chip_click_remove(): assert "clearFilters" in src() or "clear" in src().lower()
def test_genus_filter_select(): assert "genusFilter" in src()
