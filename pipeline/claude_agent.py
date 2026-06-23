"""
Step 5 — Claude Integration

Sends processed documents to Claude for:
  - question answering
  - summarisation
  - insight extraction

Each call records itself in the document's lineage trail.
"""

import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from pipeline.lineage import LineageTracker

load_dotenv()

CLIENT = anthropic.Anthropic()
MODEL = "claude-opus-4-8"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_document_context(ingested: dict) -> str:
    """
    Assembles a clean, structured prompt block from the ingested document.
    Includes metadata, text, and tables — so Claude knows what it's reading.
    """
    meta = ingested.get("metadata", {})
    lines = []

    # Document header from metadata
    lines.append("=== DOCUMENT CONTEXT ===")
    lines.append(f"Type     : {meta.get('document_type', 'unknown')}")
    lines.append(f"Client   : {meta.get('client_name', 'unknown')}")
    lines.append(f"Date     : {meta.get('document_date', 'unknown')}")
    lines.append(f"Adviser  : {meta.get('adviser', 'unknown')}")
    lines.append(f"Topics   : {', '.join(meta.get('tags', []))}")
    lines.append("")

    # Page text and tables
    for page in ingested.get("pages", []):
        lines.append(f"--- Page {page['page']} ---")
        if page.get("text"):
            lines.append(page["text"])

        for i, table in enumerate(page.get("tables", []), start=1):
            lines.append(f"\n[Table {i}]")
            lines.append(" | ".join(table["headers"]))
            lines.append("-" * 40)
            for row in table["rows"]:
                lines.append(" | ".join(row))

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core Claude call
# ---------------------------------------------------------------------------

def _call_claude(system_prompt: str, user_prompt: str) -> str:
    message = CLIENT.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Three agent functions
# ---------------------------------------------------------------------------

def ask_question(ingested: dict, question: str, processed_dir: Path) -> str:
    """Ask a specific question about the document."""
    context = _build_document_context(ingested)
    system = (
        "You are a financial document analyst. Answer questions accurately "
        "using only the information provided in the document. "
        "If the answer is not in the document, say so clearly."
    )
    user = f"{context}\n\n=== QUESTION ===\n{question}"
    answer = _call_claude(system, user)

    tracker = LineageTracker(processed_dir, ingested["file_name"])
    tracker.record(
        step="claude_qa",
        input_path=str(processed_dir / (Path(ingested["file_name"]).stem + "_ingested.json")),
        output_path="in-memory",
        summary=f"Q: {question[:80]}",
    )

    return answer


def summarise(ingested: dict, processed_dir: Path) -> str:
    """Produce a concise summary of the document."""
    context = _build_document_context(ingested)
    system = (
        "You are a financial document analyst. Write a concise summary "
        "of the document in 3–5 sentences. Cover the client, purpose, "
        "key figures, and any notable recommendations."
    )
    user = f"{context}\n\n=== TASK ===\nSummarise this document."
    summary = _call_claude(system, user)

    tracker = LineageTracker(processed_dir, ingested["file_name"])
    tracker.record(
        step="claude_summarise",
        input_path=str(processed_dir / (Path(ingested["file_name"]).stem + "_ingested.json")),
        output_path="in-memory",
        summary="Generated document summary",
    )

    return summary


def extract_insights(ingested: dict, processed_dir: Path) -> dict:
    """
    Extract structured key facts from the document.
    Returns a dict with fields like client_name, risk_profile, key_figures, recommendations.
    """
    context = _build_document_context(ingested)
    system = (
        "You are a financial document analyst. Extract key facts from the document "
        "and return them as a JSON object with these fields:\n"
        "  - client_name: string\n"
        "  - document_type: string\n"
        "  - risk_profile: string or null\n"
        "  - key_figures: list of {label, value} objects\n"
        "  - recommendations: list of strings (top 3 max)\n"
        "  - red_flags: list of strings (anything that needs attention)\n"
        "Return only valid JSON, no explanation."
    )
    user = f"{context}\n\n=== TASK ===\nExtract key insights as JSON."
    raw = _call_claude(system, user)

    # Strip markdown code fences if Claude wraps the JSON
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        insights = json.loads(cleaned)
    except json.JSONDecodeError:
        insights = {"raw_response": raw, "parse_error": "Claude did not return valid JSON"}

    tracker = LineageTracker(processed_dir, ingested["file_name"])
    tracker.record(
        step="claude_insights",
        input_path=str(processed_dir / (Path(ingested["file_name"]).stem + "_ingested.json")),
        output_path="in-memory",
        summary=f"Extracted {len(insights.get('key_figures', []))} key figures, "
                f"{len(insights.get('recommendations', []))} recommendations",
    )

    return insights


# ---------------------------------------------------------------------------
# Runner — demo all three on one document
# ---------------------------------------------------------------------------

def run_claude_agent(processed_dir: Path, file_stem: str) -> None:
    ingested_path = processed_dir / (file_stem + "_ingested.json")

    if not ingested_path.exists():
        print(f"File not found: {ingested_path}")
        return

    with open(ingested_path, "r", encoding="utf-8") as f:
        ingested = json.load(f)

    print(f"Document : {ingested['file_name']}")
    print(f"Type     : {ingested.get('metadata', {}).get('document_type', 'unknown')}")
    print("=" * 60)

    # 1. Summary
    print("\n--- SUMMARY ---")
    print(summarise(ingested, processed_dir))

    # 2. Question
    print("\n--- QUESTION ---")
    question = "What is the client's risk profile and investment timeframe?"
    print(f"Q: {question}")
    print(f"A: {ask_question(ingested, question, processed_dir)}")

    # 3. Insights
    print("\n--- INSIGHTS ---")
    insights = extract_insights(ingested, processed_dir)
    print(json.dumps(insights, indent=2))


if __name__ == "__main__":
    run_claude_agent(
        processed_dir=Path("data/processed"),
        file_stem="client_portfolio_statement",
    )
