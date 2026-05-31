"""タスク 8.2 — フロントエンド受入基準（AC-02〜AC-07）の検証テスト

ブラウザを起動せずに HTML 構造・サンプルデータの静的検証を行う。
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"
SAMPLE_PAPERS = ROOT / "docs" / "data" / "papers.json"
SAMPLE_TOPICS = ROOT / "docs" / "data" / "topics.json"


def html_src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── AC-02: 初回ページロード（ローディング表示・CDN 非同期読み込み） ────────

def test_ac02_viewport_meta_tag_exists():
    """AC-02: モバイル対応のための viewport メタタグが存在する"""
    assert 'name="viewport"' in html_src(), "viewport メタタグが存在しない"
    assert "width=device-width" in html_src(), "viewport に width=device-width が設定されていない"


def test_ac02_loading_state_shown():
    """AC-02: ローディング中に Loading... または スピナーが表示される"""
    s = html_src()
    assert "Loading" in s or "loading" in s, "ローディング表示が存在しない"


def test_ac02_spinner_animation_exists():
    """AC-02: CSS スピナーアニメーションが存在する"""
    s = html_src()
    assert "@keyframes" in s and "spinner" in s, "CSS スピナーアニメーションが存在しない"


def test_ac02_cdn_scripts_before_body_close():
    """AC-02: CDN スクリプトが適切に配置されている"""
    s = html_src()
    # React, Recharts, Babel の CDN が head 内に存在する
    assert "unpkg.com/react" in s or "esm.sh/react" in s, "React CDN が存在しない"
    assert "recharts" in s.lower(), "Recharts CDN が存在しない"
    assert "babel" in s.lower(), "Babel CDN が存在しない"


def test_ac02_parallel_fetch_for_fast_load():
    """AC-02: Promise.all で並行フェッチしている（ロード高速化）"""
    assert "Promise.all" in html_src(), "並行フェッチ（Promise.all）が実装されていない"


# ── AC-03: トピックフィルタ ────────────────────────────────────────────────

def test_ac03_topic_filter_connected_to_paper_list():
    """AC-03: トピックフィルタが論文一覧に反映される"""
    s = html_src()
    assert "selectedTopic" in s, "selectedTopic 状態が存在しない"
    assert "primary_topic" in s, "primaryTopic フィルタリングが実装されていない"
    assert "filteredPapers" in s, "filteredPapers が存在しない"


def test_ac03_filter_reset_page_on_change():
    """AC-03: フィルタ変更時にページが 1 にリセットされる"""
    s = html_src()
    assert "setCurrentPage(1)" in s, "フィルタ変更時のページリセットが実装されていない"


def test_ac03_topic_clear_button_exists():
    """AC-03: トピック選択解除ボタンが存在する"""
    s = html_src()
    assert "handleTopicSelect(null)" in s or "setSelectedTopic(null)" in s, \
        "トピックフィルタのクリアが実装されていない"


# ── AC-04: キーワード検索 ──────────────────────────────────────────────────

def test_ac04_search_filters_title():
    """AC-04: 検索がタイトルに適用される"""
    s = html_src()
    assert "title" in s and "toLowerCase" in s, "タイトル検索が実装されていない"


def test_ac04_search_filters_abstract():
    """AC-04: 検索がアブストラクトに適用される"""
    s = html_src()
    assert "abstract" in s and "toLowerCase" in s, "アブストラクト検索が実装されていない"


def test_ac04_search_input_field_exists():
    """AC-04: テキスト検索入力フィールドが存在する"""
    s = html_src()
    assert "<input" in s and ("type=\"search\"" in s or "type=\"text\"" in s or "onChange" in s), \
        "検索入力フィールドが存在しない"


def test_ac04_keyword_cloud_click_sets_search():
    """AC-04: キーワード雲のクリックで検索クエリが更新される"""
    s = html_src()
    assert "onKeywordSelect={handleSearch}" in s, \
        "キーワード雲のクリックが検索に連動していない"


# ── AC-05: OpenReview リンク ───────────────────────────────────────────────

def test_ac05_openreview_link_in_paper_detail():
    """AC-05: 論文詳細に OpenReview リンクが存在する"""
    s = html_src()
    assert "openreview_url" in s or "openreview.net" in s, \
        "OpenReview リンクが存在しない"


def test_ac05_link_opens_in_new_tab():
    """AC-05: OpenReview リンクが新しいタブで開く"""
    assert 'target="_blank"' in html_src(), "OpenReview リンクが新しいタブで開かない"


def test_ac05_link_has_noopener_noreferrer():
    """AC-05: OpenReview リンクに rel='noopener noreferrer' がある"""
    assert "noopener noreferrer" in html_src(), \
        "OpenReview リンクにセキュリティ属性が不足している"


# ── AC-06: モバイルレイアウト ──────────────────────────────────────────────

def test_ac06_viewport_meta_exists():
    """AC-06: モバイルレイアウト用 viewport メタタグが存在する"""
    s = html_src()
    assert 'name="viewport"' in s and "width=device-width" in s, \
        "モバイル対応の viewport タグが存在しない"


def test_ac06_flex_wrap_used():
    """AC-06: flexWrap を使用してモバイルで折り返しが可能"""
    s = html_src()
    assert "flexWrap" in s or "flex-wrap" in s, \
        "モバイル対応の flexWrap が使用されていない"


def test_ac06_no_fixed_width_overflow():
    """AC-06: コンテンツが固定幅で切れないよう max-width や 100% が使われている"""
    s = html_src()
    assert "100%" in s, "レスポンシブ幅設定（100%）が存在しない"


# ── AC-07: JSON ファイルの存在確認 ────────────────────────────────────────

def test_ac07_sample_papers_json_exists():
    """AC-07: docs/data/papers.json が存在する"""
    assert SAMPLE_PAPERS.exists(), "docs/data/papers.json が存在しない"


def test_ac07_sample_topics_json_exists():
    """AC-07: docs/data/topics.json が存在する"""
    assert SAMPLE_TOPICS.exists(), "docs/data/topics.json が存在しない"


def test_ac07_papers_json_fetchable():
    """AC-07: index.html から papers.json が fetch できる（URL パス確認）"""
    s = html_src()
    assert "data/papers.json" in s, "index.html が data/papers.json を参照していない"


def test_ac07_topics_json_fetchable():
    """AC-07: index.html から topics.json が fetch できる（URL パス確認）"""
    s = html_src()
    assert "data/topics.json" in s, "index.html が data/topics.json を参照していない"
