"""タスク 2.3 — papers_raw.json 保存とキャッシュスキップ機構の単体テスト"""
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from scripts.fetch_papers import (
    save_raw_papers,
    load_cached_papers,
    RawPaper,
)

ROOT = Path(__file__).parent.parent


def make_sample_papers(n: int = 3) -> list[RawPaper]:
    return [
        RawPaper(
            id=f"paper{i:03d}",
            title=f"Paper {i}",
            authors=[f"Author {i}"],
            abstract=f"Abstract {i}.",
            keywords=["kw"],
            status="Poster" if i % 2 else "Oral",
            rating_avg=float(6 + i),
            openreview_url=f"https://openreview.net/forum?id=paper{i:03d}",
        )
        for i in range(n)
    ]


# ── save_raw_papers ────────────────────────────────────────────────────────

def test_save_raw_papers_creates_file(tmp_path):
    papers = make_sample_papers(2)
    output = tmp_path / "papers_raw.json"
    save_raw_papers(papers, output)
    assert output.exists()


def test_save_raw_papers_writes_valid_json(tmp_path):
    papers = make_sample_papers(2)
    output = tmp_path / "papers_raw.json"
    save_raw_papers(papers, output)
    with output.open(encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2


def test_save_raw_papers_preserves_all_fields(tmp_path):
    papers = make_sample_papers(1)
    output = tmp_path / "papers_raw.json"
    save_raw_papers(papers, output)
    with output.open(encoding="utf-8") as f:
        data = json.load(f)
    paper = data[0]
    assert paper["id"] == "paper000"
    assert paper["title"] == "Paper 0"
    assert paper["status"] == "Oral"
    assert paper["rating_avg"] == 6.0
    assert "openreview_url" in paper


def test_save_raw_papers_creates_parent_dirs(tmp_path):
    """出力先ディレクトリが存在しなくても作成する"""
    output = tmp_path / "nested" / "deep" / "papers_raw.json"
    save_raw_papers(make_sample_papers(1), output)
    assert output.exists()


def test_save_raw_papers_overwrites_existing_file(tmp_path):
    output = tmp_path / "papers_raw.json"
    save_raw_papers(make_sample_papers(3), output)
    save_raw_papers(make_sample_papers(1), output)
    with output.open(encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1  # 上書きされている


# ── load_cached_papers ─────────────────────────────────────────────────────

def test_load_cached_papers_returns_none_when_missing(tmp_path):
    result = load_cached_papers(tmp_path / "nonexistent.json")
    assert result is None


def test_load_cached_papers_returns_data_when_exists(tmp_path):
    papers = make_sample_papers(3)
    output = tmp_path / "papers_raw.json"
    save_raw_papers(papers, output)

    loaded = load_cached_papers(output)
    assert loaded is not None
    assert len(loaded) == 3
    assert loaded[0]["id"] == "paper000"


def test_load_cached_papers_returns_full_list(tmp_path):
    papers = make_sample_papers(10)
    output = tmp_path / "papers_raw.json"
    save_raw_papers(papers, output)
    loaded = load_cached_papers(output)
    assert loaded is not None
    assert len(loaded) == 10


# ── main() — キャッシュスキップ統合テスト ──────────────────────────────────

def test_main_exits_zero_when_cache_exists(tmp_path):
    """papers_raw.json が存在する場合、API を呼ばず exit(0) する"""
    import scripts.fetch_papers as fp

    # 実際のキャッシュファイルを作成
    cache = tmp_path / "papers_raw.json"
    save_raw_papers(make_sample_papers(2), cache)

    with mock.patch.object(fp, "create_client") as mc, \
         mock.patch("sys.argv", ["fetch_papers.py", "--output", str(cache)]):
        with pytest.raises(SystemExit) as exc_info:
            fp.main()
        assert exc_info.value.code == 0  # 正常終了

    mc.assert_not_called()  # API は呼ばれていない


def test_main_exits_one_on_api_error(tmp_path):
    """API エラー発生時に exit(1) する"""
    import scripts.fetch_papers as fp

    output = tmp_path / "papers_raw.json"

    with mock.patch.object(fp, "create_client") as mc, \
         mock.patch("sys.argv", ["fetch_papers.py", "--output", str(output)]):
        mc.side_effect = Exception("Connection refused")
        with pytest.raises(SystemExit) as exc_info:
            fp.main()
        assert exc_info.value.code == 1  # エラー終了


def test_main_cli_help_exits_cleanly():
    """--help が正常終了する"""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fetch_papers.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "papers_raw.json" in result.stdout
