"""タスク 2.1 — OpenReview API 接続・全件取得の単体テスト"""
import time
from unittest import mock

import pytest

# テスト対象モジュールを import（まだ実装前なので ImportError が起きる）
from scripts.fetch_papers import create_client, fetch_all_notes, SLEEP_INTERVAL


# ── create_client ──────────────────────────────────────────────────────────

def test_create_client_returns_openreview_client():
    """正しいベース URL で OpenReviewClient を生成する"""
    with mock.patch("scripts.fetch_papers.openreview.api.OpenReviewClient") as MockClient:
        MockClient.return_value = mock.MagicMock()
        client = create_client()
        MockClient.assert_called_once_with(baseurl="https://api2.openreview.net")


def test_create_client_accepts_custom_base_url():
    """カスタム base_url を受け付ける"""
    with mock.patch("scripts.fetch_papers.openreview.api.OpenReviewClient") as MockClient:
        MockClient.return_value = mock.MagicMock()
        create_client(base_url="https://custom.url")
        MockClient.assert_called_once_with(baseurl="https://custom.url")


# ── fetch_all_notes ────────────────────────────────────────────────────────

def _make_mock_client(pages: list[list]) -> mock.MagicMock:
    """get_notes が pages リストを順に返すモッククライアントを生成する"""
    client = mock.MagicMock()
    client.get_notes.side_effect = pages
    return client


def test_fetch_returns_empty_list_when_no_notes():
    """ノートが 0 件のとき空リストを返す"""
    client = _make_mock_client([[]])
    result = fetch_all_notes(client, "ICLR.cc/2026/Conference")
    assert result == []


def test_fetch_calls_get_notes_with_correct_first_params():
    """最初のリクエストに正しい invitation・content・details・offset を使う"""
    client = _make_mock_client([[]])
    with mock.patch("time.sleep"):
        fetch_all_notes(client, "ICLR.cc/2026/Conference")
    client.get_notes.assert_called_with(
        invitation="ICLR.cc/2026/Conference/-/Submission",
        content={"venueid": "ICLR.cc/2026/Conference"},
        details="directReplies",
        limit=1000,
        offset=0,
    )


def test_fetch_paginates_until_empty_page():
    """空ページが返るまでページネーションを続ける（各ページが満杯の場合）"""
    page1 = [mock.MagicMock(id=f"note{i}") for i in range(1000)]
    page2 = [mock.MagicMock(id=f"note{i}") for i in range(1000, 2000)]  # 満杯ページ → 続行
    page3 = []  # 空ページ → 終了
    client = _make_mock_client([page1, page2, page3])

    with mock.patch("time.sleep"):
        result = fetch_all_notes(client, "ICLR.cc/2026/Conference")

    assert len(result) == 2000
    assert client.get_notes.call_count == 3


def test_fetch_paginates_stops_when_partial_page():
    """最終ページが limit 未満なら追加リクエストしない"""
    page1 = [mock.MagicMock(id=f"note{i}") for i in range(1000)]
    page2 = [mock.MagicMock(id=f"note{i}") for i in range(1000, 1200)]  # 200件 < 1000
    client = _make_mock_client([page1, page2])

    with mock.patch("time.sleep"):
        result = fetch_all_notes(client, "ICLR.cc/2026/Conference")

    assert len(result) == 1200
    assert client.get_notes.call_count == 2


def test_fetch_sets_correct_offsets():
    """ページごとに offset が正しく増加する"""
    page1 = [mock.MagicMock() for _ in range(1000)]
    page2 = [mock.MagicMock() for _ in range(500)]
    client = _make_mock_client([page1, page2])

    with mock.patch("time.sleep"):
        fetch_all_notes(client, "ICLR.cc/2026/Conference", limit=1000)

    calls = client.get_notes.call_args_list
    assert calls[0].kwargs["offset"] == 0
    assert calls[1].kwargs["offset"] == 1000


def test_fetch_sleeps_between_requests():
    """リクエスト間に SLEEP_INTERVAL 秒のスリープを挿入する"""
    page1 = [mock.MagicMock() for _ in range(1000)]
    page2 = []
    client = _make_mock_client([page1, page2])

    with mock.patch("time.sleep") as mock_sleep:
        fetch_all_notes(client, "ICLR.cc/2026/Conference")

    # ページ取得のたびに sleep が呼ばれる
    assert mock_sleep.call_count >= 1
    for call in mock_sleep.call_args_list:
        assert call.args[0] == SLEEP_INTERVAL


def test_fetch_uses_no_authentication():
    """認証なし（baseurl のみ）でクライアントを生成できる"""
    with mock.patch("scripts.fetch_papers.openreview.api.OpenReviewClient") as MockClient:
        MockClient.return_value = mock.MagicMock()
        client = create_client()
        # username / password が渡されていないことを確認
        call_kwargs = MockClient.call_args.kwargs
        assert "username" not in call_kwargs
        assert "password" not in call_kwargs
