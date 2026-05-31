"""
classify_topics.py — Gemini API で ICLR 2026 論文をトピック分類する

Usage:
    uv run scripts/classify_topics.py [--input INPUT] [--output OUTPUT] [--topics TOPICS]
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Annotated, Any

from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel, Field

# ── 定数 ─────────────────────────────────────────────────────────────────

MODEL_NAME = "gemini-3.5-flash"
DEFAULT_INPUT = "data/papers_raw.json"
DEFAULT_OUTPUT = "data/papers_classified.json"
DEFAULT_TOPICS = "data/topics.json"
DEFAULT_CHECKPOINT = "data/.classify_checkpoint.json"
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_RETRIES = 3
MAX_RETRIES = DEFAULT_MAX_RETRIES      # エイリアス（テスト用）
INITIAL_RETRY_DELAY = 1.0              # 秒: 最初のリトライ待機時間
REDUCED_BATCH_SIZE = 25                # JSON エラー時の縮小バッチサイズ
ERROR_RATE_THRESHOLD = 0.15            # エラー率 15% でビルド中断
INTER_BATCH_SLEEP = 2.0               # バッチ間のスリープ秒数（レート制限対策）


# ── Pydantic モデル（Structured Output スキーマ） ─────────────────────────

class TopicAssignment(BaseModel):
    """1 論文のトピック分類結果"""
    paper_id: str
    primary_topic: str
    secondary_topics: Annotated[list[str], Field(max_length=2)]


class ClassificationBatch(BaseModel):
    """1 バッチ分の分類結果リスト"""
    results: list[TopicAssignment]


# ── Gemini API クライアント ────────────────────────────────────────────────

def create_gemini_client() -> genai.Client:
    """
    環境変数 GEMINI_API_KEY から Gemini API クライアントを初期化する。
    キーが設定されていない場合は KeyError を送出する。
    """
    api_key = os.environ["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


# ── プロンプト構築 ─────────────────────────────────────────────────────────

def build_classification_prompt(
    papers: list[dict[str, Any]],
    topic_definitions: list[dict[str, Any]],
) -> str:
    """
    論文リストとトピック定義から Gemini API 向けの分類プロンプトを生成する。
    各論文にトピックを 1〜3 件付与するよう指示する。
    """
    topics_block = "\n".join(
        f"  {t['id']}: {t['name']} — {t['description']}"
        for t in topic_definitions
    )

    papers_block = "\n\n".join(
        f"  paper_id: {p['id']}\n"
        f"  title: {p['title']}\n"
        f"  keywords: {', '.join(p.get('keywords', []))}\n"
        f"  abstract: {p.get('abstract', '')[:300]}"
        for p in papers
    )

    return f"""You are an expert in machine learning research. Classify each paper into the most relevant research topics.

Available topics:
{topics_block}

Papers to classify:
{papers_block}

For each paper, assign:
- primary_topic: the single most relevant topic ID (e.g., "T-01")
- secondary_topics: 0 to 2 additional relevant topic IDs (empty list if none)

Return results as JSON matching the provided schema. Include every paper_id in the results."""


# ── バッチ分類 ────────────────────────────────────────────────────────────

def classify_batch(
    client: genai.Client,
    papers: list[dict[str, Any]],
    topic_definitions: list[dict[str, Any]],
) -> ClassificationBatch:
    """
    論文リストを Gemini API で一括分類し ClassificationBatch を返す。

    - response_mime_type="application/json" + response_schema=ClassificationBatch で
      スキーマを強制する（Gemini API ネイティブ structured output）。
    """
    prompt = build_classification_prompt(papers, topic_definitions)

    config = genai_types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ClassificationBatch,
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )

    return ClassificationBatch.model_validate_json(response.text)


def classify_batch_with_retry(
    client: genai.Client,
    papers: list[dict[str, Any]],
    topic_definitions: list[dict[str, Any]],
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
) -> ClassificationBatch | None:
    """
    classify_batch を指数バックオフ＋ジッター付きでリトライする。

    - API エラー / JSON パースエラー: 最大 max_retries 回リトライ
    - リトライ間隔: initial_delay * 2^attempt + jitter（1s → 2s → 4s）
    - 全リトライ失敗時: None を返す
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return classify_batch(client, papers, topic_definitions)
        except Exception as e:
            if attempt < max_retries - 1:
                jitter = random.uniform(0, delay * 0.25)
                time.sleep(delay + jitter)
                delay *= 2

    return None  # 全リトライ失敗


# ── エラー率計算 ────────────────────────────────────────────────────────────

def calculate_error_rate(null_count: int, total_processed: int) -> float:
    """エラー率（null_count / total_processed）を返す。total_processed が 0 の場合は 0.0"""
    if total_processed == 0:
        return 0.0
    return null_count / total_processed


# ── Checkpoint 管理 ────────────────────────────────────────────────────────

def load_checkpoint(checkpoint_path: Path) -> dict[str, Any]:
    """checkpoint ファイルが存在すれば読み込む（なければ空 dict）"""
    if not checkpoint_path.exists():
        return {}
    with checkpoint_path.open(encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(checkpoint: dict[str, Any], checkpoint_path: Path) -> None:
    """checkpoint を JSON ファイルに保存する"""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint_path.open("w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


# ── バッチ処理ループ ───────────────────────────────────────────────────────

def run_batch_classification(
    papers: list[dict[str, Any]],
    topic_definitions: list[dict[str, Any]],
    client: genai.Client,
    batch_size: int = DEFAULT_BATCH_SIZE,
    checkpoint_path: Path = Path(DEFAULT_CHECKPOINT),
) -> list[dict[str, Any]]:
    """
    papers を batch_size 件ずつ Gemini API に送信してトピック分類を行う。

    - checkpoint ファイルで処理済み論文をスキップし、中断後の再開を保証する。
    - 各バッチ完了後に checkpoint を保存する。
    - 全処理完了後に RawPaper + 分類結果を結合したリストを返す。
    """
    checkpoint = load_checkpoint(checkpoint_path)

    # 未処理論文のみ抽出してバッチ分類
    unprocessed = [p for p in papers if p["id"] not in checkpoint]

    null_count = 0
    total_processed = 0

    if unprocessed:
        for start in range(0, len(unprocessed), batch_size):
            batch = unprocessed[start : start + batch_size]
            batch_num = start // batch_size + 1
            print(f"[classify] バッチ {batch_num}: {len(batch)} 件を処理中...")
            # レート制限対策: バッチ間スリープ（初回はスキップ）
            if start > 0:
                time.sleep(INTER_BATCH_SLEEP)

            result = classify_batch_with_retry(client, batch, topic_definitions)

            if result is None and len(batch) > REDUCED_BATCH_SIZE:
                # フルサイズ失敗 → 半分サイズで再分割して再試行
                print(f"[classify] ⚠ バッチ {batch_num} 失敗: {REDUCED_BATCH_SIZE} 件に分割して再試行...")
                for sub_start in range(0, len(batch), REDUCED_BATCH_SIZE):
                    sub = batch[sub_start: sub_start + REDUCED_BATCH_SIZE]
                    sub_result = classify_batch_with_retry(client, sub, topic_definitions)
                    if sub_result is not None:
                        for assignment in sub_result.results:
                            checkpoint[assignment.paper_id] = assignment.model_dump()
                        total_processed += len(sub_result.results)
                    else:
                        null_count += len(sub)
                        total_processed += len(sub)
            elif result is None:
                # 小サイズでも失敗 → null
                null_count += len(batch)
                total_processed += len(batch)
                print(f"[classify] ⚠ バッチ {batch_num} 失敗: {len(batch)} 件を null に設定")
            else:
                for assignment in result.results:
                    checkpoint[assignment.paper_id] = assignment.model_dump()
                total_processed += len(result.results)

            save_checkpoint(checkpoint, checkpoint_path)
            print(f"[classify] checkpoint 保存済み ({len(checkpoint)} / {len(papers)} 件)")

            # エラー率チェック（最低 200 件処理後から有効化）
            if total_processed >= 200:
                rate = calculate_error_rate(null_count, total_processed)
                if rate > ERROR_RATE_THRESHOLD:
                    print(
                        f"[classify] ❌ エラー率 {rate:.1%} が閾値 {ERROR_RATE_THRESHOLD:.0%} を超過。"
                        f" null: {null_count} / {total_processed}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
    else:
        print(f"[classify] 全 {len(papers)} 件が checkpoint 済みです。スキップします。")

    # RawPaper と分類結果を結合
    classified: list[dict[str, Any]] = []
    for paper in papers:
        assignment = checkpoint.get(paper["id"])
        if assignment:
            classified.append({
                **paper,
                "primary_topic": assignment["primary_topic"],
                "secondary_topics": assignment.get("secondary_topics", []),
            })
        else:
            classified.append({
                **paper,
                "primary_topic": None,
                "secondary_topics": [],
            })

    return classified


# ── CLI ──────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gemini API を用いて ICLR 2026 論文をトピック分類し papers_classified.json に保存する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  uv run scripts/classify_topics.py
  uv run scripts/classify_topics.py --input data/papers_raw.json --output data/papers_classified.json
        """,
    )
    parser.add_argument("--input", default=DEFAULT_INPUT,
                        help=f"入力ファイル（デフォルト: {DEFAULT_INPUT}）")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"出力ファイル（デフォルト: {DEFAULT_OUTPUT}）")
    parser.add_argument("--topics", default=DEFAULT_TOPICS,
                        help=f"トピック定義 JSON（デフォルト: {DEFAULT_TOPICS}）")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"1 リクエストあたりの論文数（デフォルト: {DEFAULT_BATCH_SIZE}）")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    topics_path = Path(args.topics)
    checkpoint_path = Path(DEFAULT_CHECKPOINT)

    # 入力ファイル確認
    if not input_path.exists():
        print(f"[classify_topics] エラー: {input_path} が存在しません。先に fetch_papers.py を実行してください。",
              file=sys.stderr)
        sys.exit(1)
    if not topics_path.exists():
        print(f"[classify_topics] エラー: {topics_path} が存在しません。", file=sys.stderr)
        sys.exit(1)

    # データ読み込み
    with input_path.open(encoding="utf-8") as f:
        papers = json.load(f)
    with topics_path.open(encoding="utf-8") as f:
        topic_definitions = json.load(f)["topics"]

    print(f"[classify_topics] 入力: {len(papers)} 件 / モデル: {MODEL_NAME}")
    print(f"[classify_topics] トピック定義: {len(topic_definitions)} 件")

    # Gemini クライアント初期化
    try:
        client = create_gemini_client()
    except KeyError:
        print("[classify_topics] エラー: GEMINI_API_KEY 環境変数が設定されていません。", file=sys.stderr)
        print("  export GEMINI_API_KEY=your_key  または  GEMINI_API_KEY=xxx uv run scripts/classify_topics.py",
              file=sys.stderr)
        sys.exit(1)

    # バッチ分類実行
    classified = run_batch_classification(
        papers=papers,
        topic_definitions=topic_definitions,
        client=client,
        batch_size=args.batch_size,
        checkpoint_path=checkpoint_path,
    )

    # 結果保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    classified_count = sum(1 for p in classified if p.get("primary_topic"))
    print(f"[classify_topics] 完了: {classified_count} / {len(classified)} 件を分類 → {output_path}")


if __name__ == "__main__":
    main()
