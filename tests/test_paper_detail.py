"""論文詳細表示テスト（Vanilla JS 版 — abstract expand in card）"""
from pathlib import Path
ROOT = Path(__file__).parent.parent
def src(): return (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

def test_abstract_expand_on_click(): assert "classList.toggle" in src() or "toggle(" in src()
def test_abstract_class_exists(): assert 'class="abstract"' in src()
def test_openreview_link(): assert "openreview_url" in src() and "OpenReview" in src()
def test_link_target_blank(): assert 'target="_blank"' in src()
def test_link_noopener(): assert "noopener noreferrer" in src()
def test_shows_rating(): assert "rating_avg" in src()
def test_shows_status_badge(): assert 'class="badge' in src()
def test_shows_authors(): assert "authors" in src()
def test_shows_title(): assert "title" in src() and 'class="title"' in src()
def test_shows_topics(): assert "topic-chip" in src() or "topics" in src()
def test_paper_hover_effect(): assert "hover" in src() or ":hover" in src()
