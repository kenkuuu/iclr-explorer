"""タスク 6.1 — TopicDistribution コンポーネント（Treemap + BarChart）の構造テスト"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML = ROOT / "docs" / "index.html"


def src() -> str:
    return HTML.read_text(encoding="utf-8")


# ── コンポーネント定義 ─────────────────────────────────────────────────────

def test_topic_distribution_component_defined():
    assert "TopicDistribution" in src(), "TopicDistribution コンポーネントが定義されていない"


def test_topic_distribution_is_function():
    s = src()
    assert "function TopicDistribution" in s or "TopicDistribution = (" in s, \
        "TopicDistribution が関数として定義されていない"


def test_topic_distribution_accepts_topics_prop():
    s = src()
    idx = s.find("TopicDistribution")
    context = s[idx: idx + 200]
    assert "topics" in context, "TopicDistribution が topics プロップを受け取っていない"


def test_topic_distribution_accepts_on_topic_select_prop():
    s = src()
    assert "onTopicSelect" in s, "onTopicSelect コールバックが存在しない"


# ── Recharts Treemap ───────────────────────────────────────────────────────

def test_uses_recharts_treemap():
    s = src()
    assert "Treemap" in s, "Recharts Treemap が使用されていない"


def test_treemap_uses_paper_count_as_data_key():
    s = src()
    assert "paper_count" in s or "size" in s, \
        "Treemap の dataKey に paper_count または size が使用されていない"


def test_treemap_has_click_handler():
    s = src()
    treemap_idx = s.find("Treemap")
    assert treemap_idx != -1
    context = s[treemap_idx: treemap_idx + 400]
    assert "onClick" in context or "onTopicSelect" in context, \
        "Treemap にクリックハンドラが設定されていない"


# ── Recharts BarChart ─────────────────────────────────────────────────────

def test_uses_recharts_bar_chart():
    s = src()
    assert "BarChart" in s, "Recharts BarChart が使用されていない"


def test_bar_chart_has_bar_element():
    s = src()
    assert "<Bar" in s or "Bar " in s, "BarChart に Bar 要素が存在しない"


def test_bar_chart_sorted_by_paper_count():
    s = src()
    assert "paper_count" in s
    assert "sort" in s, "BarChart のデータがソートされていない"


def test_bar_chart_has_click_handler():
    s = src()
    bar_idx = s.find("<Bar")
    if bar_idx == -1:
        bar_idx = s.find("BarChart")
    assert bar_idx != -1
    context = s[bar_idx: bar_idx + 500]
    assert "onClick" in context, "BarChart の Bar にクリックハンドラが設定されていない"


# ── Recharts デストラクチャリング ──────────────────────────────────────────

def test_recharts_components_destructured():
    s = src()
    assert "Recharts" in s, "Recharts が読み込まれていない"
    assert "Treemap" in s and "BarChart" in s, \
        "Treemap と BarChart がどちらも使用されていない"


def test_responsive_container_used():
    s = src()
    assert "ResponsiveContainer" in s, "ResponsiveContainer が使用されていない"


# ── レンダリング確認 ───────────────────────────────────────────────────────

def test_topic_distribution_rendered_in_app():
    s = src()
    # App の return 内に TopicDistribution が使われている
    return_idx = s.rfind("return (")
    if return_idx == -1:
        return_idx = s.rfind("return(")
    assert return_idx != -1
    after_return = s[return_idx:]
    assert "TopicDistribution" in after_return, \
        "App の return 内で TopicDistribution が使われていない"


def test_topic_distribution_receives_topics_and_handler():
    s = src()
    # App の JSX 内で topics と onTopicSelect が渡されている
    assert "topics={topics}" in s or "topics = {topics}" in s, \
        "TopicDistribution に topics={topics} が渡されていない"
    assert "onTopicSelect" in s, "TopicDistribution に onTopicSelect が渡されていない"
