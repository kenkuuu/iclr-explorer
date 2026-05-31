"""タスク 2.2 — directReplies パース・メタデータ抽出の単体テスト（ICLR 2026 実構造対応版）"""
import openreview

from scripts.fetch_papers import (
    is_accepted,
    get_status,
    parse_rating,
    get_rating_avg,
    parse_note,
    filter_and_parse_notes,
    DEFAULT_VENUE_ID,
)


# ── テスト用ノート生成ヘルパー ──────────────────────────────────────────────

def make_note(
    note_id: str = "test001",
    title: str = "Test Paper",
    abstract: str = "Abstract text.",
    authors: list[str] | None = None,
    keywords: list[str] | None = None,
    venue: str = "ICLR 2026 Poster",
    venueid: str = "ICLR.cc/2026/Conference",
    ratings: list[int] | None = None,
) -> openreview.api.Note:
    """ICLR 2026 実構造を模したテスト用 Note を生成する"""
    if authors is None:
        authors = ["Author One", "Author Two"]
    if keywords is None:
        keywords = ["machine learning", "deep learning"]

    direct_replies = []
    if ratings is not None:
        for i, rating in enumerate(ratings):
            direct_replies.append({
                "id": f"review_{i}",
                "parentInvitations": "ICLR.cc/2026/Conference/-/Official_Review",
                "invitations": [f"ICLR.cc/2026/Conference/Submission1/-/Official_Review"],
                "content": {
                    "rating": {"value": rating},
                    "soundness": {"value": 3},
                    "confidence": {"value": 3},
                },
                "signatures": [f"~Reviewer{i}"],
            })

    return openreview.api.Note(
        id=note_id,
        content={
            "title": {"value": title},
            "abstract": {"value": abstract},
            "authors": {"value": authors},
            "keywords": {"value": keywords},
            "venue": {"value": venue},
            "venueid": {"value": venueid},
        },
        details={"directReplies": direct_replies},
    )


# ── is_accepted ────────────────────────────────────────────────────────────

def test_is_accepted_returns_true_for_accepted_paper():
    note = make_note(venueid="ICLR.cc/2026/Conference")
    assert is_accepted(note) is True


def test_is_accepted_returns_false_for_rejected_paper():
    note = make_note(venueid="ICLR.cc/2026/Conference/Rejected")
    assert is_accepted(note) is False


def test_is_accepted_returns_false_for_empty_venueid():
    note = make_note(venueid="")
    assert is_accepted(note) is False


def test_is_accepted_returns_false_for_different_conference():
    note = make_note(venueid="NeurIPS.cc/2026/Conference")
    assert is_accepted(note) is False


# ── get_status ─────────────────────────────────────────────────────────────

def test_get_status_oral_from_venue_text():
    assert get_status("ICLR 2026 Oral") == "Oral"


def test_get_status_poster_from_venue_text():
    assert get_status("ICLR 2026 Poster") == "Poster"


def test_get_status_spotlight_defaults_to_poster():
    assert get_status("ICLR 2026 Spotlight") == "Poster"


def test_get_status_defaults_to_poster_for_unknown():
    assert get_status("Unknown venue") == "Poster"


# ── parse_rating ───────────────────────────────────────────────────────────

def test_parse_rating_from_dict_value():
    """ICLR 2026 形式: {'value': 8} → 8.0"""
    assert parse_rating({"value": 8}) == 8.0


def test_parse_rating_from_int():
    assert parse_rating(7) == 7.0


def test_parse_rating_from_float():
    assert parse_rating(6.5) == 6.5


def test_parse_rating_from_string_colon_format():
    """旧形式との互換性: '6: marginally above...' → 6.0"""
    assert parse_rating("6: marginally above acceptance threshold") == 6.0


def test_parse_rating_returns_none_for_invalid():
    assert parse_rating("N/A") is None
    assert parse_rating(None) is None


# ── get_rating_avg ─────────────────────────────────────────────────────────

def test_get_rating_avg_with_multiple_reviews():
    """parentInvitations で Official_Review を識別し平均を計算する"""
    note = make_note(ratings=[8, 6, 7])
    avg = get_rating_avg(note)
    assert abs(avg - 7.0) < 1e-6


def test_get_rating_avg_with_single_review():
    note = make_note(ratings=[9])
    assert get_rating_avg(note) == 9.0


def test_get_rating_avg_returns_zero_when_no_reviews():
    note = make_note()  # ratings=None
    assert get_rating_avg(note) == 0.0


def test_get_rating_avg_ignores_non_review_replies():
    """Official_Review 以外の directReplies はスキップする"""
    note = make_note(ratings=[8])
    # 非レビューの reply を追加
    note.details["directReplies"].append({
        "parentInvitations": "ICLR.cc/2026/Conference/-/Meta_Review",
        "content": {"rating": {"value": 1}},  # これは集計されない
    })
    avg = get_rating_avg(note)
    assert avg == 8.0  # 非レビューの 1 は含まれない


# ── parse_note ─────────────────────────────────────────────────────────────

def test_parse_note_returns_none_for_rejected():
    note = make_note(venueid="ICLR.cc/2026/Conference/Rejected")
    assert parse_note(note) is None


def test_parse_note_returns_raw_paper_for_accepted():
    note = make_note(
        note_id="paper001",
        title="Great Paper",
        abstract="Great abstract.",
        authors=["Alice", "Bob"],
        keywords=["RL", "LLM"],
        venue="ICLR 2026 Oral",
        venueid="ICLR.cc/2026/Conference",
        ratings=[8, 7],
    )
    result = parse_note(note)
    assert result is not None
    assert result["id"] == "paper001"
    assert result["title"] == "Great Paper"
    assert result["abstract"] == "Great abstract."
    assert result["authors"] == ["Alice", "Bob"]
    assert result["keywords"] == ["RL", "LLM"]
    assert result["status"] == "Oral"
    assert abs(result["rating_avg"] - 7.5) < 1e-6
    assert result["openreview_url"] == "https://openreview.net/forum?id=paper001"


def test_parse_note_poster_status():
    note = make_note(venue="ICLR 2026 Poster", ratings=[6])
    result = parse_note(note)
    assert result is not None
    assert result["status"] == "Poster"


def test_parse_note_no_reviewer_info_in_output():
    """個別レビュアーの情報（signatures 等）が出力に含まれない"""
    note = make_note(venue="ICLR 2026 Poster", ratings=[6])
    result = parse_note(note)
    assert result is not None
    result_str = str(result)
    assert "Reviewer" not in result_str


def test_parse_note_no_pdf_url_in_output():
    """PDF URL が出力に含まれない（著作権保護）"""
    note = make_note(venue="ICLR 2026 Poster")
    result = parse_note(note)
    assert result is not None
    assert "pdf" not in result


# ── filter_and_parse_notes ────────────────────────────────────────────────

def test_filter_and_parse_notes_returns_only_accepted():
    notes = [
        make_note(note_id="a1", venue="ICLR 2026 Oral", ratings=[8],
                  venueid="ICLR.cc/2026/Conference"),
        make_note(note_id="a2", venueid="ICLR.cc/2026/Conference/Rejected"),
        make_note(note_id="a3", venue="ICLR 2026 Poster", ratings=[6],
                  venueid="ICLR.cc/2026/Conference"),
    ]
    result = filter_and_parse_notes(notes)
    assert len(result) == 2
    ids = {p["id"] for p in result}
    assert ids == {"a1", "a3"}


def test_filter_and_parse_notes_correct_oral_poster_counts():
    notes = [
        make_note(note_id="o1", venue="ICLR 2026 Oral", ratings=[8],
                  venueid="ICLR.cc/2026/Conference"),
        make_note(note_id="o2", venue="ICLR 2026 Oral", ratings=[9],
                  venueid="ICLR.cc/2026/Conference"),
        make_note(note_id="p1", venue="ICLR 2026 Poster", ratings=[6],
                  venueid="ICLR.cc/2026/Conference"),
    ]
    result = filter_and_parse_notes(notes)
    oral = [p for p in result if p["status"] == "Oral"]
    poster = [p for p in result if p["status"] == "Poster"]
    assert len(oral) == 2
    assert len(poster) == 1
