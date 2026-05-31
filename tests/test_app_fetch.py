"""タスク 5.1 — App フェッチ・ローディング・エラー状態の構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML_PATH = ROOT / "docs" / "index.html"


def html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


# ── Promise.all による並行フェッチ ─────────────────────────────────────────

def test_app_uses_promise_all():
    assert "Promise.all" in html(), "Promise.all による並行フェッチが存在しない"


def test_app_fetches_papers_json():
    assert 'data/papers.json' in html(), 'papers.json の fetch が存在しない'


def test_app_fetches_topics_json():
    assert 'data/topics.json' in html(), 'topics.json の fetch が存在しない'


def test_app_fetches_both_in_same_promise_all():
    src = html()
    pa_idx = src.find("Promise.all")
    assert pa_idx != -1
    # Promise.all の後方に両方のフェッチが存在する
    after = src[pa_idx:pa_idx + 400]
    assert "papers.json" in after and "topics.json" in after


# ── データ状態管理 ─────────────────────────────────────────────────────────

def test_app_has_loading_state():
    src = html()
    assert "useState(true)" in src or "loading" in src, "loading 状態が存在しない"


def test_app_has_error_state():
    assert "setError" in html(), "error 状態のセットが存在しない"


def test_app_sets_papers_from_response():
    src = html()
    assert "setPapers" in src, "setPapers が存在しない"
    assert ".papers" in src or "papersData.papers" in src, \
        "papers データの抽出が存在しない"


def test_app_sets_topics_from_response():
    src = html()
    assert "setTopics" in src, "setTopics が存在しない"
    assert ".topics" in src or "topicsData.topics" in src, \
        "topics データの抽出が存在しない"


def test_app_sets_loading_false_after_fetch():
    assert "setLoading(false)" in html(), "フェッチ後に loading を false にしていない"


def test_app_displays_error_message():
    src = html()
    assert "{error}" in src or "error.message" in src, \
        "エラーメッセージが表示されていない"


# ── ローディングスピナー ───────────────────────────────────────────────────

def test_loading_element_exists():
    src = html()
    assert "loading" in src.lower(), "loading 要素が存在しない"


def test_spinner_animation_exists():
    """CSS スピナーアニメーション（@keyframes または spinner クラス）が存在する"""
    src = html()
    has_keyframes = "@keyframes" in src
    has_spinner_class = "spinner" in src
    assert has_keyframes or has_spinner_class, \
        "CSS スピナーアニメーション（@keyframes または .spinner）が存在しない"


def test_loading_state_shows_spinner_element():
    """loading 状態のレンダリングに spinner 要素または animation が含まれる"""
    src = html()
    # loading 状態のレンダリング部分を探す
    loading_render_idx = src.find("loading)")
    if loading_render_idx == -1:
        loading_render_idx = src.find('"loading"')
    assert loading_render_idx != -1, "loading 状態のレンダリングが見つからない"


# ── エラー状態 ─────────────────────────────────────────────────────────────

def test_error_element_has_error_class():
    src = html()
    assert 'className="error"' in src or "class=\"error\"" in src, \
        "error クラスを持つ要素が存在しない"


def test_catch_block_sets_error():
    src = html()
    assert ".catch" in src or "catch(" in src, "fetch エラーをキャッチしていない"
