"""Phylogeny Tree フィルタ統合テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_tree_list_container(): assert 'id="treeList"' in src()
def test_builds_tree(): assert "buildTree" in src()
def test_tree_node_class(): assert "tree-node" in src()
def test_tree_row_class(): assert "tree-row" in src()
def test_tree_row_clickable(): assert "addEventListener" in src() and "treeList" in src()  # listener bound in buildTree()
def test_set_state_from_depth(): assert "setStateFromDepth" in src() or "state[" in src()
def test_state_has_phylum(): assert 'state' in src() and 'phylum' in src()
def test_state_has_class(): assert 'state' in src() and '"class"' in src() or "state.class" in src()
def test_state_has_genus(): assert "genus" in src()
def test_clear_state(): assert "clearStateFromDepth" in src() or "state[" in src()
def test_lineage_chart(): assert "lineageChart" in src()
def test_show_lineage(): assert "showLineage" in src()
def test_active_class_on_select(): s=src(); assert "classList.add" in s and "active" in s
def test_has_topic_section(): assert 'id="phylogeny"' in src()
def test_filtered_uses_state(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+600]; assert "state" in ctx
def test_has_topic_tree(): assert "tree-row" in src() and "tree-count" in src()
def test_paper_list_has_papers_id(): assert 'id="papers"' in src()
def test_filter_shows_phylum_in_results(): assert "phylumFilter" in src() and "phylumChart" in src()
