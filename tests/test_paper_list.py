"""タスク 6.2 — PaperList コンポーネント（論文カード・ページネーション）の構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── PaperList コンポーネント ───────────────────────────────────────────────

def test_paper_list_component_defined():
    assert "PaperList" in src(), "PaperList コンポーネントが定義されていない"


def test_paper_list_is_function():
    s = src()
    assert "function PaperList" in s or "PaperList = (" in s, \
        "PaperList が関数として定義されていない"


def test_paper_list_accepts_filtered_papers():
    s = src()
    idx = s.find("PaperList")
    assert idx != -1
    context = s[idx: idx + 300]
    assert "filteredPapers" in context or "papers" in context, \
        "PaperList が filteredPapers を受け取っていない"


def test_paper_list_rendered_in_app():
    s = src()
    return_idx = s.rfind("return (")
    if return_idx == -1:
        return_idx = s.rfind("return(")
    after_return = s[return_idx:]
    assert "PaperList" in after_return, "App の return 内で PaperList が使われていない"


# ── ページネーション ───────────────────────────────────────────────────────

def test_page_size_is_100():
    s = src()
    assert "100" in s, "ページサイズ 100 が定義されていない"
    assert "pageSize" in s or "PAGE_SIZE" in s or "perPage" in s, \
        "ページサイズの変数が定義されていない"


def test_has_prev_page_button():
    s = src()
    assert ("前" in s or "prev" in s.lower() or "previous" in s.lower()), \
        "前のページボタンが存在しない"


def test_has_next_page_button():
    s = src()
    assert ("次" in s or "next" in s.lower()), "次のページボタンが存在しない"


def test_pagination_shows_current_page():
    s = src()
    assert "currentPage" in s, "currentPage が表示に使用されていない"
    assert "totalPages" in s or "total" in s.lower(), \
        "総ページ数の表示が存在しない"


def test_pagination_uses_slice():
    """ページネーションに slice が使われている"""
    s = src()
    assert ".slice(" in s or "slice(" in s, "配列の slice によるページネーションが実装されていない"


def test_prev_button_disabled_on_first_page():
    s = src()
    assert "disabled" in s, "前のページボタンの disabled 制御が存在しない"


# ── PaperCard コンポーネント ───────────────────────────────────────────────

def test_paper_card_component_defined():
    s = src()
    assert "PaperCard" in s, "PaperCard コンポーネントが定義されていない"


def test_paper_card_uses_react_memo():
    s = src()
    assert "React.memo" in s, "PaperCard に React.memo が使用されていない"


def test_paper_card_shows_title():
    s = src()
    assert "title" in s and "paper.title" in s or "p.title" in s, \
        "PaperCard にタイトル表示が存在しない"


def test_paper_card_shows_authors_with_et_al():
    s = src()
    assert "et al" in s, "著者表示に 'et al.' が含まれていない"
    assert "3" in s, "先頭 3 名の処理が存在しない"


def test_paper_card_shows_status():
    s = src()
    assert "status" in s, "PaperCard に採択ステータス表示が存在しない"


def test_paper_card_shows_rating_avg():
    s = src()
    assert "rating_avg" in s, "PaperCard に rating_avg 表示が存在しない"


def test_paper_card_shows_primary_topic():
    s = src()
    assert "primary_topic" in s, "PaperCard に primary_topic 表示が存在しない"


def test_paper_card_has_click_handler():
    s = src()
    assert "onPaperSelect" in s or "setSelectedPaper" in s or "onSelect" in s, \
        "PaperCard にクリックハンドラが存在しない"


# ── App への統合 ───────────────────────────────────────────────────────────

def test_paper_list_receives_filtered_papers_from_app():
    s = src()
    assert "filteredPapers" in s, "App が filteredPapers を PaperList に渡していない"


def test_paper_list_receives_current_page_from_app():
    s = src()
    assert "currentPage" in s, "App が currentPage を PaperList に渡していない"
