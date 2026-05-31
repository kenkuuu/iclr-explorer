"""データフェッチ・ローディング構造テスト（Vanilla JS 版）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_uses_promise_all(): assert "Promise.all" in src()
def test_fetches_papers(): assert "papers.json" in src()
def test_fetches_topics(): assert "topics.json" in src()
def test_fetches_phylogeny(): assert "phylogeny.json" in src()
def test_parallel_fetch(): s=src(); idx=s.find("Promise.all"); ctx=s[idx:idx+200]; assert "papers.json" in ctx
def test_error_handling(): assert ".catch" in src() or "catch(" in src()
def test_has_papers_global(): assert "PAPERS" in src()
def test_has_tree_global(): assert "TREE" in src()
def test_renders_papers(): assert "renderResults" in src()
def test_build_kpis(): assert "buildKpis" in src() or "kpis" in src()
def test_init_on_load(): assert "init()" in src() or "init(" in src()
def test_total_submissions_constant(): assert "TOTAL_SUBMISSIONS" in src()
def test_openreview_link(): assert "openreview.net" in src()
def test_noopener_noreferrer(): assert "noopener noreferrer" in src()
