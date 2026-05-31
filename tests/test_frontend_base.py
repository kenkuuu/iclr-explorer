"""タスク 1.3 — フロントエンド HTML ベースと GitHub Pages 構成の検証テスト"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX_HTML = ROOT / "docs" / "index.html"
SAMPLE_PAPERS = ROOT / "docs" / "data" / "papers.json"
SAMPLE_TOPICS = ROOT / "docs" / "data" / "topics.json"


def html_source() -> str:
    assert INDEX_HTML.exists(), "docs/index.html が存在しない"
    return INDEX_HTML.read_text(encoding="utf-8")


# ── HTML 構造 ──────────────────────────────────────────────────────────────

def test_index_html_exists():
    assert INDEX_HTML.exists(), "docs/index.html が存在しない"


def test_index_html_has_root_div():
    assert 'id="root"' in html_source(), '<div id="root"> が存在しない'


def test_index_html_has_babel_script_tag():
    assert 'type="text/babel"' in html_source(), 'type="text/babel" スクリプトタグが存在しない'


def test_index_html_shows_loading_text():
    assert "Loading" in html_source(), '"Loading" テキストが HTML 内に存在しない'


# ── CDN インポート ──────────────────────────────────────────────────────────

def test_index_html_imports_react():
    src = html_source()
    assert "react" in src.lower(), "React の CDN import が存在しない"


def test_index_html_imports_react_dom():
    src = html_source()
    assert "react-dom" in src.lower(), "ReactDOM の CDN import が存在しない"


def test_index_html_imports_recharts():
    src = html_source()
    assert "recharts" in src.lower(), "Recharts の CDN import が存在しない"


def test_index_html_imports_babel():
    src = html_source()
    assert "babel" in src.lower(), "Babel Standalone の CDN import が存在しない"


# ── 帰属表示 ───────────────────────────────────────────────────────────────

def test_index_html_has_openreview_attribution():
    src = html_source()
    assert "OpenReview" in src, "OpenReview への帰属表示が存在しない"


def test_index_html_has_cc0_or_license_mention():
    src = html_source()
    assert "CC0" in src or "openreview.net" in src, "CC0 またはデータ出典の記述が存在しない"


# ── サンプルデータ ─────────────────────────────────────────────────────────

def test_sample_papers_json_exists():
    assert SAMPLE_PAPERS.exists(), "docs/data/papers.json が存在しない"


def test_sample_papers_json_is_valid():
    with SAMPLE_PAPERS.open(encoding="utf-8") as f:
        data = json.load(f)
    assert "meta" in data
    assert "papers" in data
    assert len(data["papers"]) >= 3, "サンプル論文が 3 件未満"
    paper = data["papers"][0]
    for field in ["id", "title", "authors", "abstract", "keywords", "status", "rating_avg",
                  "primary_topic", "secondary_topics", "openreview_url"]:
        assert field in paper, f"papers[0] に {field} フィールドが存在しない"


def test_sample_topics_json_exists():
    assert SAMPLE_TOPICS.exists(), "docs/data/topics.json が存在しない"


def test_sample_topics_json_has_paper_count():
    with SAMPLE_TOPICS.open(encoding="utf-8") as f:
        data = json.load(f)
    assert "topics" in data
    assert len(data["topics"]) >= 3, "サンプルトピックが 3 件未満"
    topic = data["topics"][0]
    assert "paper_count" in topic, "topics[0] に paper_count が存在しない（build 出力形式が必要）"
