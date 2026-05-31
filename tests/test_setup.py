"""タスク 1.1 — プロジェクト基盤セットアップの検証テスト"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parent.parent


def test_required_directories_exist():
    assert (ROOT / "data").is_dir(), "data/ ディレクトリが存在しない"
    assert (ROOT / "docs" / "data").is_dir(), "docs/data/ ディレクトリが存在しない"
    assert (ROOT / "scripts").is_dir(), "scripts/ ディレクトリが存在しない"


def test_env_example_has_gemini_key():
    env_example = ROOT / ".env.example"
    assert env_example.exists(), ".env.example が存在しない"
    assert "GEMINI_API_KEY" in env_example.read_text(), ".env.example に GEMINI_API_KEY が含まれていない"


def test_gitignore_excludes_checkpoint():
    gitignore = ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore が存在しない"
    assert ".classify_checkpoint.json" in gitignore.read_text(), ".gitignore に checkpoint が含まれていない"


def test_fetch_papers_script_exists():
    assert (ROOT / "scripts" / "fetch_papers.py").exists(), "scripts/fetch_papers.py が存在しない"


def test_fetch_papers_help_exits_cleanly():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fetch_papers.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--help が正常終了しない: {result.stderr}"


def test_required_packages_importable():
    import openreview  # noqa: F401
    from google import genai  # noqa: F401
    import pydantic  # noqa: F401
    import pandas  # noqa: F401
