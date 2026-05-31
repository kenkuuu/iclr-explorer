"""タスク 6.3 — PaperDetail モーダルコンポーネントの構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── コンポーネント定義 ─────────────────────────────────────────────────────

def test_paper_detail_component_defined():
    assert "PaperDetail" in src(), "PaperDetail コンポーネントが定義されていない"


def test_paper_detail_is_function():
    s = src()
    assert "function PaperDetail" in s or "PaperDetail = (" in s, \
        "PaperDetail が関数として定義されていない"


def test_paper_detail_returns_null_when_no_paper():
    """paper が null のとき null を返す"""
    s = src()
    idx = s.find("PaperDetail")
    assert idx != -1
    context = s[idx: idx + 200]
    assert "null" in context, "PaperDetail が null ガードを持っていない"


# ── モーダルの表示内容 ─────────────────────────────────────────────────────

def test_paper_detail_shows_title():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "title" in context, "PaperDetail にタイトル表示が存在しない"


def test_paper_detail_shows_all_authors():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "authors" in context, "PaperDetail に著者表示が存在しない"
    # 全著者を表示（先頭 3 名 + et al. ではなく全員）
    assert ".join" in context or "map" in context, \
        "PaperDetail で著者全員が表示されていない（join または map が必要）"


def test_paper_detail_shows_abstract():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "abstract" in context, "PaperDetail にアブストラクト表示が存在しない"


def test_paper_detail_shows_rating_avg():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "rating_avg" in context, "PaperDetail に rating_avg 表示が存在しない"


def test_paper_detail_shows_status():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "status" in context, "PaperDetail に採択ステータス表示が存在しない"


def test_paper_detail_shows_primary_topic():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "primary_topic" in context, "PaperDetail に primary_topic 表示が存在しない"


# ── OpenReview リンク ──────────────────────────────────────────────────────

def test_paper_detail_has_openreview_link():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "openreview_url" in context or "openreview" in context.lower(), \
        "PaperDetail に OpenReview リンクが存在しない"


def test_openreview_link_has_noopener_noreferrer():
    s = src()
    assert 'rel="noopener noreferrer"' in s or "noopener noreferrer" in s, \
        "OpenReview リンクに rel='noopener noreferrer' が存在しない"


def test_openreview_link_opens_in_new_tab():
    s = src()
    assert 'target="_blank"' in s, "OpenReview リンクが新しいタブで開かない"


# ── 閉じるボタン ─────────────────────────────────────────────────────────

def test_paper_detail_has_close_button():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "onClose" in context or "close" in context.lower(), \
        "PaperDetail に閉じるボタンが存在しない"


def test_close_sets_selected_paper_null():
    s = src()
    assert "setSelectedPaper(null)" in s, \
        "閉じる操作で selectedPaper を null に設定していない"


# ── モーダルオーバーレイ ───────────────────────────────────────────────────

def test_paper_detail_has_overlay():
    s = src()
    idx = s.find("function PaperDetail")
    context = s[idx: idx + 4000]
    assert "overlay" in context.lower() or "modal" in context.lower(), \
        "PaperDetail にモーダルオーバーレイが存在しない"


def test_modal_stops_propagation():
    s = src()
    assert "stopPropagation" in s, "モーダル内クリックの stopPropagation が実装されていない"


# ── App への統合 ───────────────────────────────────────────────────────────

def test_paper_detail_rendered_conditionally_in_app():
    s = src()
    assert "selectedPaper" in s and "PaperDetail" in s, \
        "App で selectedPaper 条件付き PaperDetail が使用されていない"
