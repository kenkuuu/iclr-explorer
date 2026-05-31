"""タスク 6.4 — KeywordCloud コンポーネントの構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


def component_src() -> str:
    """KeywordCloud 関数定義の前後 3000 文字"""
    s = src()
    idx = s.find("function KeywordCloud")
    assert idx != -1, "KeywordCloud が未定義"
    return s[idx: idx + 3000]


# ── コンポーネント定義 ─────────────────────────────────────────────────────

def test_keyword_cloud_component_defined():
    assert "KeywordCloud" in src(), "KeywordCloud コンポーネントが定義されていない"


def test_keyword_cloud_is_function():
    s = src()
    assert "function KeywordCloud" in s, "KeywordCloud が関数として定義されていない"


def test_keyword_cloud_accepts_papers_prop():
    ctx = component_src()
    assert "papers" in ctx, "KeywordCloud が papers プロップを受け取っていない"


def test_keyword_cloud_accepts_on_keyword_select_prop():
    s = src()
    assert "onKeywordSelect" in s, "onKeywordSelect コールバックが存在しない"


# ── キーワード集計ロジック ─────────────────────────────────────────────────

def test_keyword_cloud_counts_keywords():
    ctx = component_src()
    assert "keywords" in ctx, "keywords フィールドの集計が存在しない"


def test_keyword_cloud_counts_per_keyword():
    ctx = component_src()
    # カウント集計（辞書形式かカウンター形式）
    assert "count" in ctx.lower() or "freq" in ctx.lower() or "counts" in ctx, \
        "キーワード出現頻度の集計が存在しない"


def test_keyword_cloud_takes_top_100():
    ctx = component_src()
    assert "100" in ctx, "上位 100 件の制限が存在しない"
    assert "slice" in ctx or ".slice(" in ctx, "上位抽出に slice が使われていない"


def test_keyword_cloud_sorts_by_frequency():
    ctx = component_src()
    assert "sort" in ctx, "キーワードのソートが存在しない"


# ── フォントサイズ ──────────────────────────────────────────────────────────

def test_keyword_cloud_uses_font_size():
    ctx = component_src()
    assert "fontSize" in ctx or "font-size" in ctx, \
        "フォントサイズの設定が存在しない"


def test_keyword_cloud_min_font_size_12():
    ctx = component_src()
    assert "12" in ctx, "最小フォントサイズ 12px が設定されていない"


def test_keyword_cloud_max_font_size_36():
    ctx = component_src()
    assert "36" in ctx, "最大フォントサイズ 36px が設定されていない"


# ── クリックハンドラ ───────────────────────────────────────────────────────

def test_keyword_cloud_has_click_handler():
    ctx = component_src()
    assert "onClick" in ctx, "キーワードにクリックハンドラが存在しない"


def test_keyword_click_calls_on_keyword_select():
    ctx = component_src()
    assert "onKeywordSelect" in ctx, \
        "キーワードクリックで onKeywordSelect が呼ばれていない"


# ── App への統合 ───────────────────────────────────────────────────────────

def test_keyword_cloud_rendered_in_app():
    s = src()
    return_idx = s.rfind("return (")
    after_return = s[return_idx:]
    assert "KeywordCloud" in after_return, "App の return 内で KeywordCloud が使われていない"


def test_keyword_cloud_receives_papers_from_app():
    s = src()
    # papers={papers} または papers={filteredPapers} が渡されている
    assert "papers={papers}" in s or "papers={filteredPapers}" in s, \
        "App が papers を KeywordCloud に渡していない"


def test_keyword_cloud_receives_handler_from_app():
    s = src()
    assert "onKeywordSelect" in s, "App が onKeywordSelect を KeywordCloud に渡していない"


# ── null ガード ────────────────────────────────────────────────────────────

def test_keyword_cloud_handles_empty_papers():
    ctx = component_src()
    assert "null" in ctx or "length" in ctx or "length === 0" in ctx, \
        "KeywordCloud に空データのガード処理が存在しない"
