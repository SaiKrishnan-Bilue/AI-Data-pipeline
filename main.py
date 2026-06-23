"""
Main entry point — Financial Advisor AI Pipeline

Runs the full pipeline or individual stages via command line.

Usage:
  python main.py                          # process all documents (full pipeline)
  python main.py --doc financial_plan     # process one document
  python main.py --ask "What is the client's risk profile?" --doc financial_plan
  python main.py --summarise --doc risk_assessment
  python main.py --insights --doc investment_proposal
"""

import argparse
import json
from pathlib import Path

from pipeline.ingestion import run_ingestion, ingest_document
from pipeline.metadata import run_metadata_tagging, build_metadata
from pipeline.lineage import LineageTracker, retrofit_existing_documents
from pipeline.claude_agent import ask_question, summarise, extract_insights

SAMPLE_DOCS_DIR = Path("data/sample_docs")
PROCESSED_DIR   = Path("data/processed")
RESPONSES_DIR   = Path("outputs/responses")


# ---------------------------------------------------------------------------
# Full pipeline — runs all stages on every document
# ---------------------------------------------------------------------------

def run_full_pipeline() -> None:
    print("\n== STAGE 1: Ingestion ==")
    run_ingestion(SAMPLE_DOCS_DIR, PROCESSED_DIR)

    print("\n== STAGE 2: Metadata Tagging ==")
    run_metadata_tagging(PROCESSED_DIR)

    print("\n== STAGE 3: Lineage Tracking ==")
    retrofit_existing_documents(PROCESSED_DIR, SAMPLE_DOCS_DIR)

    print("\n== STAGE 4: Claude — Summarise All Documents ==")
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

    for ingested_path in sorted(PROCESSED_DIR.glob("*_ingested.json")):
        with open(ingested_path, "r", encoding="utf-8") as f:
            ingested = json.load(f)

        file_stem = Path(ingested["file_name"]).stem
        print(f"\nProcessing: {ingested['file_name']}")

        summary = summarise(ingested, PROCESSED_DIR)
        insights = extract_insights(ingested, PROCESSED_DIR)

        response = {
            "file_name": ingested["file_name"],
            "metadata": ingested.get("metadata", {}),
            "summary": summary,
            "insights": insights,
        }

        out_path = RESPONSES_DIR / (file_stem + "_response.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        print(f"  Saved: {out_path}")

    print("\n== Pipeline complete ==")
    print(f"Responses saved to: {RESPONSES_DIR}")


# ---------------------------------------------------------------------------
# Single document helpers
# ---------------------------------------------------------------------------

def _load_or_ingest(doc_stem: str) -> dict:
    """Load an already-processed doc, or ingest it fresh if not found."""
    ingested_path = PROCESSED_DIR / (doc_stem + "_ingested.json")

    if ingested_path.exists():
        with open(ingested_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Try to find the source file
    for ext in (".pdf", ".docx"):
        source = SAMPLE_DOCS_DIR / (doc_stem + ext)
        if source.exists():
            print(f"Ingesting {source.name} on the fly...")
            ingested = ingest_document(source)
            ingested["metadata"] = build_metadata(ingested)

            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
            with open(ingested_path, "w", encoding="utf-8") as f:
                json.dump(ingested, f, indent=2, ensure_ascii=False)

            tracker = LineageTracker(PROCESSED_DIR, source.name)
            tracker.record(
                step="ingestion",
                input_path=str(source),
                output_path=str(ingested_path),
                summary=f"Extracted {ingested['page_count']} page(s), {ingested['total_characters']:,} chars",
            )
            tracker.record(
                step="metadata_tagging",
                input_path=str(ingested_path),
                output_path=str(ingested_path),
                summary=f"Classified as '{ingested['metadata'].get('document_type')}'",
            )
            return ingested

    raise FileNotFoundError(
        f"No source document found for '{doc_stem}' in {SAMPLE_DOCS_DIR}"
    )


def _save_response(doc_stem: str, data: dict) -> Path:
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESPONSES_DIR / (doc_stem + "_response.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Financial Advisor AI Pipeline"
    )
    parser.add_argument("--doc",       type=str, help="Document stem, e.g. financial_plan")
    parser.add_argument("--ask",       type=str, help="Ask a question about the document")
    parser.add_argument("--summarise", action="store_true", help="Summarise the document")
    parser.add_argument("--insights",  action="store_true", help="Extract structured insights")
    args = parser.parse_args()

    # No flags — run the full pipeline
    if not any([args.doc, args.ask, args.summarise, args.insights]):
        run_full_pipeline()
        return

    # Single-document mode requires --doc
    if not args.doc:
        print("Error: --doc is required when using --ask, --summarise, or --insights")
        return

    ingested = _load_or_ingest(args.doc)
    print(f"\nDocument : {ingested['file_name']}")
    print(f"Type     : {ingested.get('metadata', {}).get('document_type', 'unknown')}")
    print("=" * 60)

    if args.ask:
        print(f"\nQ: {args.ask}")
        answer = ask_question(ingested, args.ask, PROCESSED_DIR)
        print(f"A: {answer}")
        _save_response(args.doc, {"question": args.ask, "answer": answer})

    elif args.summarise:
        result = summarise(ingested, PROCESSED_DIR)
        print(f"\n{result}")
        _save_response(args.doc, {"summary": result})

    elif args.insights:
        result = extract_insights(ingested, PROCESSED_DIR)
        print(f"\n{json.dumps(result, indent=2)}")
        _save_response(args.doc, {"insights": result})

    else:
        # --doc alone: run all three
        print("\n--- SUMMARY ---")
        summary = summarise(ingested, PROCESSED_DIR)
        print(summary)

        print("\n--- INSIGHTS ---")
        insights = extract_insights(ingested, PROCESSED_DIR)
        print(json.dumps(insights, indent=2))

        _save_response(args.doc, {"summary": summary, "insights": insights})


if __name__ == "__main__":
    main()
