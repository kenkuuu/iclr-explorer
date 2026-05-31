"""タスク 6.5 — StatsSummary コンポーネントの構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


def component_src() -> str:
    """StatsSummary 関数定義の前後 3000 文字"""
    s = src()
    idx = s.find("function StatsSummary")
    assert idx != -1, "StatsSummary が未定義"
    return s[idx: idx + 3000]


# ── コンポーネント定義 ─────────────────────────────────────────────────────

def test_stats_summary_component_defined():
    assert "StatsSummary" in src(), "StatsSummary コンポーネントが定義されていない"


def test_stats_summary_is_function():
    s = src()
    assert "function StatsSummary" in s, "StatsSummary が関数として定義されていない"


def test_stats_summary_accepts_papers_prop():
    ctx = component_src()
    assert "papers" in ctx, "StatsSummary が papers プロップを受け取っていない"


# ── 数値カード ────────────────────────────────────────────────────────────

def test_stats_summary_shows_total_papers():
    ctx = component_src()
    assert "total" in ctx.lower() or "length" in ctx or "totalPapers" in ctx, \
        "StatsSummary に総論文数の表示が存在しない"


def test_stats_summary_shows_oral_count():
    ctx = component_src()
    assert "Oral" in ctx, "StatsSummary に Oral 件数の表示が存在しない"
    assert "oralCount" in ctx or '"Oral"' in ctx, "Oral 件数の集計が存在しない"


def test_stats_summary_shows_poster_count():
    ctx = component_src()
    assert "Poster" in ctx, "StatsSummary に Poster 件数の表示が存在しない"
    assert "posterCount" in ctx or '"Poster"' in ctx, "Poster 件数の集計が存在しない"


def test_stats_summary_shows_rating_average():
    ctx = component_src()
    assert "rating_avg" in ctx or "avgRating" in ctx, \
        "StatsSummary に rating 平均の計算・表示が存在しない"
    assert "toFixed" in ctx or "avg" in ctx.lower(), \
        "rating 平均の数値整形が存在しない"


# ── スコア分布チャート ─────────────────────────────────────────────────────

def test_stats_summary_has_bar_chart():
    ctx = component_src()
    assert "BarChart" in ctx, "StatsSummary にスコア分布 BarChart が存在しない"


def test_stats_summary_chart_has_data():
    ctx = component_src()
    assert "count" in ctx or "data" in ctx, \
        "BarChart のデータが存在しない"


def test_stats_summary_chart_has_bar_element():
    ctx = component_src()
    assert "<Bar" in ctx or "Bar " in ctx, "BarChart に Bar 要素が存在しない"


def test_stats_summary_has_score_bins():
    """スコアをビン（区間）で集計している"""
    ctx = component_src()
    has_bins = "bin" in ctx.lower() or "filter" in ctx or "range" in ctx
    assert has_bins, "スコアのビン化集計が存在しない"


# ── App への統合 ───────────────────────────────────────────────────────────

def test_stats_summary_rendered_in_app():
    s = src()
    return_idx = s.rfind("return (")
    after_return = s[return_idx:]
    assert "StatsSummary" in after_return, "App の return 内で StatsSummary が使われていない"


def test_stats_summary_receives_papers_from_app():
    s = src()
    assert "papers={papers}" in s, "App が papers を StatsSummary に渡していない"


# ── null ガード ────────────────────────────────────────────────────────────

def test_stats_summary_handles_empty_papers():
    ctx = component_src()
    assert "null" in ctx or "length" in ctx, \
        "StatsSummary に空データのガード処理が存在しない"
