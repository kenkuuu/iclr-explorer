"""受入基準（AC-02〜AC-07）構造テスト（Vanilla JS 版）"""
import json
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
PAPERS_PATH   = ROOT / "docs" / "data" / "papers.json"
PHYLO_PATH    = ROOT / "docs" / "data" / "phylogeny.json"
TOPICS_PATH   = ROOT / "docs" / "data" / "topics.json"

# AC-02: ロード・スピナー
def test_ac02_viewport(): assert "width=device-width" in src()
def test_ac02_parallel_fetch(): assert "Promise.all" in src()
def test_ac02_cdn_chart(): assert "chart.js" in src().lower()
def test_ac02_error_handling(): assert ".catch" in src()

# AC-03: トピックフィルタ
def test_ac03_phylum_filter(): assert "phylumFilter" in src() and "function filtered" in src()
def test_ac03_page_reset(): assert "page=1" in src() or "page = 1" in src()
def test_ac03_clear_filter(): assert "clearFilters" in src()

# AC-04: キーワード検索
def test_ac04_title_search(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+1000]; assert "title" in ctx
def test_ac04_abstract_search(): s=src(); idx=s.find("function filtered"); ctx=s[idx:idx+1000]; assert "abstract" in ctx
def test_ac04_search_input(): assert 'id="q"' in src()

# AC-05: OpenReview リンク
def test_ac05_openreview_link(): assert "openreview_url" in src()
def test_ac05_target_blank(): assert 'target="_blank"' in src()
def test_ac05_noopener(): assert "noopener noreferrer" in src()

# AC-06: モバイル対応
def test_ac06_viewport(): assert "width=device-width" in src()
def test_ac06_responsive_css(): assert "@media" in src()
def test_ac06_max_width(): assert "max-width" in src()

# AC-07: JSON ファイル存在
def test_ac07_papers_json_exists(): assert PAPERS_PATH.exists()
def test_ac07_papers_json_valid():
    with PAPERS_PATH.open(encoding="utf-8") as f: d = json.load(f)
    assert "papers" in d and len(d["papers"]) > 0
def test_ac07_phylogeny_json_exists(): assert PHYLO_PATH.exists()
def test_ac07_topics_json_exists(): assert TOPICS_PATH.exists()
def test_ac07_papers_json_has_topics():
    with PAPERS_PATH.open(encoding="utf-8") as f: d = json.load(f)
    assert any("topics" in p for p in d["papers"][:100])
def test_ac07_all_papers_have_primary_phylum():
    with PAPERS_PATH.open(encoding="utf-8") as f: d = json.load(f)
    no_phylum = [p for p in d["papers"] if not p.get("primary_phylum")]
    assert len(no_phylum) == 0, f"{len(no_phylum)} papers have no primary_phylum"
