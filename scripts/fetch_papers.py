"""
fetch_papers.py — OpenReview API v2 から ICLR 2026 採択論文のメタデータを取得する

Usage:
    uv run scripts/fetch_papers.py [--venue-id VENUE_ID] [--output OUTPUT] [--force]
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import openreview
from typing import TypedDict

# API 設定
OPENREVIEW_BASE_URL = "https://api2.openreview.net"
DEFAULT_VENUE_ID = "ICLR.cc/2026/Conference"
DEFAULT_OUTPUT = "data/papers_raw.json"
PAGE_LIMIT = 1000
SLEEP_INTERVAL = 0.5  # 秒: リクエスト間のスリープ（レート制限への配慮）


# ── データ型定義 ────────────────────────────────────────────────────────────

class RawPaper(TypedDict):
    """papers_raw.json の 1 論文エントリ"""
    id: str
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]
    status: str          # "Oral" | "Poster"
    rating_avg: float
    openreview_url: str


# ── directReplies パース関数群 ──────────────────────────────────────────────

def is_accepted(note: openreview.api.Note, venue_id: str = DEFAULT_VENUE_ID) -> bool:
    """
    note.content.venueid.value が venue_id と一致すれば採択と判定する。
    ICLR 2026 では Decision ノードではなく venueid フィールドで採択を判定する。
    """
    content = getattr(note, "content", {}) or {}
    venueid_raw = content.get("venueid", "")
    venueid = venueid_raw.get("value", "") if isinstance(venueid_raw, dict) else str(venueid_raw)
    return venueid == venue_id


def get_status(venue_text: str) -> str:
    """
    venue テキスト（例: 'ICLR 2026 Oral', 'ICLR 2026 Poster'）から
    'Oral' または 'Poster' を返す。
    """
    if "Oral" in venue_text or "oral" in venue_text:
        return "Oral"
    return "Poster"


def parse_rating(rating_value: Any) -> float | None:
    """
    レーティング値を float に変換する。
    - {'value': 8} 形式: value を取り出す
    - '6: marginally...' 形式: コロン前の数値を抽出する（旧形式との互換性）
    - 数値: そのまま変換
    """
    if isinstance(rating_value, dict):
        rating_value = rating_value.get("value")
    if rating_value is None:
        return None
    try:
        return float(rating_value)
    except (ValueError, TypeError):
        try:
            return float(str(rating_value).split(":")[0].strip())
        except (ValueError, AttributeError):
            return None


def get_rating_avg(note: openreview.api.Note) -> float:
    """
    Official_Review ノードから rating 平均を計算する（レビュアー情報は除外）。
    ICLR 2026 では parentInvitations で Official_Review を識別し、
    content.rating.value（{'value': N} 形式）を使用する。
    """
    ratings: list[float] = []
    details = getattr(note, "details", None) or {}
    for reply in details.get("directReplies", []):
        parent = reply.get("parentInvitations", "") or ""
        invitations = reply.get("invitations", []) or []
        # parentInvitations（文字列）または invitations（リスト）で識別
        is_review = (
            "Official_Review" in str(parent) or
            any("Official_Review" in str(inv) for inv in invitations)
        )
        if not is_review:
            continue
        rating_raw = reply.get("content", {}).get("rating", "")
        value = parse_rating(rating_raw)
        if value is not None:
            ratings.append(value)
    return sum(ratings) / len(ratings) if ratings else 0.0


def parse_note(note: openreview.api.Note) -> RawPaper | None:
    """OpenReview note → RawPaper。採択論文でなければ None を返す。"""
    if not is_accepted(note):
        return None

    content = getattr(note, "content", {}) or {}

    def val(field: str) -> Any:
        """content フィールドの値を取得する（{"value": ...} 形式に対応）"""
        raw = content.get(field, "")
        if isinstance(raw, dict):
            return raw.get("value", "")
        return raw

    # Oral/Poster は content.venue.value から取得（例: 'ICLR 2026 Poster'）
    venue_text = str(val("venue"))
    status = get_status(venue_text)

    return RawPaper(
        id=note.id,
        title=str(val("title")),
        authors=list(val("authors") or []),
        abstract=str(val("abstract")),
        keywords=list(val("keywords") or []),
        status=status,
        rating_avg=get_rating_avg(note),
        openreview_url=f"https://openreview.net/forum?id={note.id}",
    )


def filter_and_parse_notes(notes: list[openreview.api.Note]) -> list[RawPaper]:
    """notes リストから採択論文のみを抽出し RawPaper リストに変換する"""
    results: list[RawPaper] = []
    for note in notes:
        paper = parse_note(note)
        if paper is not None:
            results.append(paper)
    return results


# ── 保存・キャッシュ関数 ────────────────────────────────────────────────────

def save_raw_papers(papers: list[RawPaper], output_path: Path) -> None:
    """採択論文リストを JSON ファイルに保存する（親ディレクトリを自動作成）"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(list(papers), f, ensure_ascii=False, indent=2)
    print(f"[fetch_papers] {len(papers)} 件を {output_path} に保存しました。")


def load_cached_papers(output_path: Path) -> list[RawPaper] | None:
    """キャッシュファイルが存在すれば読み込む（なければ None）"""
    if not output_path.exists():
        return None
    with output_path.open(encoding="utf-8") as f:
        return json.load(f)


def create_client(base_url: str = OPENREVIEW_BASE_URL) -> openreview.api.OpenReviewClient:
    """匿名アクセスで OpenReview API v2 クライアントを生成する（認証不要）"""
    return openreview.api.OpenReviewClient(baseurl=base_url)


def fetch_all_notes(
    client: openreview.api.OpenReviewClient,
    venue_id: str,
    limit: int = PAGE_LIMIT,
    sleep_interval: float = SLEEP_INTERVAL,
) -> list[Any]:
    """
    OpenReview API から venue_id の全 Submission notes を取得する。

    - limit 件ずつページネーションし、空ページが返るまで繰り返す。
    - リクエスト間に sleep_interval 秒のスリープを挿入する（レート制限配慮）。
    - directReplies を含める（Review ノードの rating 取得に必要）。
    - content={'venueid': venue_id} で採択論文のみを直接取得する（ICLR 2026 対応）。
    """
    invitation = f"{venue_id}/-/Submission"
    all_notes: list[Any] = []
    offset = 0

    while True:
        time.sleep(sleep_interval)
        notes = client.get_notes(
            invitation=invitation,
            content={"venueid": venue_id},  # 採択論文のみ取得（ICLR 2026 では venueid で判定）
            details="directReplies",
            limit=limit,
            offset=offset,
        )
        if not notes:
            break

        all_notes.extend(notes)
        print(f"  取得済み: {len(all_notes)} 件...", flush=True)

        if len(notes) < limit:
            # 最終ページ（limit 未満 = これ以上ない）
            break
        offset += limit

    return all_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenReview API v2 から ICLR 2026 採択論文のメタデータを取得し papers_raw.json に保存する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  uv run scripts/fetch_papers.py
  uv run scripts/fetch_papers.py --venue-id ICLR.cc/2026/Conference --output data/papers_raw.json
  uv run scripts/fetch_papers.py --force  # キャッシュを無視して再取得
        """,
    )
    parser.add_argument(
        "--venue-id",
        default=DEFAULT_VENUE_ID,
        help="OpenReview のベニュー ID（デフォルト: ICLR.cc/2026/Conference）",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="出力先 JSON ファイルパス（デフォルト: data/papers_raw.json）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="出力ファイルが存在しても再取得する",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_path = Path(args.output)

    # キャッシュスキップ
    if output_path.exists() and not args.force:
        print(f"[fetch_papers] キャッシュが存在します: {output_path}")
        print("[fetch_papers] --force を指定すると再取得します。")
        sys.exit(0)

    print(f"[fetch_papers] venue_id={args.venue_id}")
    print("[fetch_papers] OpenReview API に接続中...")

    try:
        client = create_client()
        notes = fetch_all_notes(client, args.venue_id)
    except Exception as e:
        print(f"[fetch_papers] エラー: API 取得に失敗しました — {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[fetch_papers] 合計 {len(notes)} 件の Submission notes を取得しました。")
    print("[fetch_papers] 採択論文をフィルタリング中...")

    papers = filter_and_parse_notes(notes)
    oral = sum(1 for p in papers if p["status"] == "Oral")
    poster = sum(1 for p in papers if p["status"] == "Poster")

    print(f"[fetch_papers] 採択論文: {len(papers)} 件 (Oral: {oral} / Poster: {poster})")

    save_raw_papers(papers, output_path)


if __name__ == "__main__":
    main()
