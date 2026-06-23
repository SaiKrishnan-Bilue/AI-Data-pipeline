"""
Step 4 — Data Lineage Tracking

Records a timestamped history of every step applied to each document.
Each document gets its own _lineage.json file in data/processed/.

Usage from any pipeline step:
    tracker = LineageTracker("data/processed", "my_document.pdf")
    tracker.record(
        step="my_step",
        input_path="data/processed/my_document_ingested.json",
        output_path="data/processed/my_document_ingested.json",
        summary="Did something useful",
        status="success",
    )
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path


def _make_lineage_id(file_name: str) -> str:
    """Stable ID derived from the file name — same file always gets the same ID."""
    return hashlib.md5(file_name.encode()).hexdigest()[:12]


class LineageTracker:
    def __init__(self, processed_dir: Path, file_name: str):
        self.processed_dir = Path(processed_dir)
        self.file_name = file_name
        self.lineage_path = self.processed_dir / (Path(file_name).stem + "_lineage.json")
        self._record = self._load_or_create()

    def _load_or_create(self) -> dict:
        if self.lineage_path.exists():
            with open(self.lineage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "lineage_id": _make_lineage_id(self.file_name),
            "file_name": self.file_name,
            "created_at": datetime.now().isoformat(),
            "events": [],
        }

    def record(self, step: str, input_path: str, output_path: str,
               summary: str, status: str = "success") -> None:
        event = {
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "input": input_path,
            "output": output_path,
            "summary": summary,
        }
        self._record["events"].append(event)
        self._save()
        print(f"  [lineage] {step} → {status}: {summary}")

    def _save(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        with open(self.lineage_path, "w", encoding="utf-8") as f:
            json.dump(self._record, f, indent=2, ensure_ascii=False)

    def get(self) -> dict:
        return self._record


def retrofit_existing_documents(processed_dir: Path, sample_docs_dir: Path) -> None:
    """
    Builds lineage records for documents already processed in steps 2 and 3.
    Reads the ingested JSON files to reconstruct what happened.
    """
    ingested_files = sorted(processed_dir.glob("*_ingested.json"))

    if not ingested_files:
        print(f"No ingested files found in {processed_dir}")
        return

    for ingested_path in ingested_files:
        with open(ingested_path, "r", encoding="utf-8") as f:
            ingested = json.load(f)

        file_name = ingested["file_name"]
        source_path = str(sample_docs_dir / file_name)
        output_path = str(ingested_path)
        metadata = ingested.get("metadata", {})

        tracker = LineageTracker(processed_dir, file_name)

        # Only add events if this lineage record is brand new
        if not tracker._record["events"]:
            tracker.record(
                step="ingestion",
                input_path=source_path,
                output_path=output_path,
                summary=(
                    f"Extracted {ingested['page_count']} page(s), "
                    f"{ingested.get('total_tables', 0)} table(s), "
                    f"{ingested['total_characters']:,} chars"
                ),
            )

            if metadata:
                tracker.record(
                    step="metadata_tagging",
                    input_path=output_path,
                    output_path=output_path,
                    summary=(
                        f"Classified as '{metadata.get('document_type', 'unknown')}', "
                        f"client: {metadata.get('client_name', 'unknown')}, "
                        f"tags: {', '.join(metadata.get('tags', []))}"
                    ),
                )

        print(f"Lineage record ready: {tracker.lineage_path.name}")

    print(f"\nAll lineage files saved to {processed_dir}")


if __name__ == "__main__":
    retrofit_existing_documents(
        processed_dir=Path("data/processed"),
        sample_docs_dir=Path("data/sample_docs"),
    )
