"""
Step 3 — Metadata Tagging

Reads each ingested JSON file, extracts structured metadata using
pattern matching, and saves an updated JSON with a metadata block added.

Note: this is rules-based extraction (regex + keywords), not AI.
Claude comes in Step 5 — by then each document will carry this metadata
as context so Claude knows what it's reading before it starts.
"""

import json
import re
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Document type classification
# ---------------------------------------------------------------------------

DOCUMENT_TYPE_RULES = [
    ("portfolio_statement", ["portfolio statement", "quarterly statement", "holdings"]),
    ("investment_proposal",  ["investment proposal", "recommended portfolio", "fee disclosure"]),
    ("financial_plan",       ["financial plan", "statement of advice", "soa", "net worth"]),
    ("risk_assessment",      ["risk assessment", "risk profile", "risk tolerance", "risk profiling"]),
]


def classify_document_type(text: str) -> str:
    lowered = text.lower()
    for doc_type, keywords in DOCUMENT_TYPE_RULES:
        if any(kw in lowered for kw in keywords):
            return doc_type
    return "unknown"


# ---------------------------------------------------------------------------
# Field extraction via regex
# ---------------------------------------------------------------------------

CLIENT_PATTERNS = [
    r"Client[:\s]+([A-Z][a-zA-Z\s&]+?)(?:\n|Account|Adviser|Date|Prepared)",
    r"Prepared for[:\s]+([A-Z][a-zA-Z\s]+?)(?:\n|Prepared by)",
]

DATE_PATTERNS = [
    r"Date[:\s]+(\d{1,2}\s+\w+\s+\d{4})",
    r"Statement Period[:\s]+.+?–\s*(.+?)(?:\n|$)",
    r"Plan Date[:\s]+(\d{1,2}\s+\w+\s+\d{4})",
    r"Date Completed[:\s]+(\d{1,2}\s+\w+\s+\d{4})",
    r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
]

ADVISER_PATTERNS = [
    r"(?:Adviser|Prepared by|Advisory firm)[:\s]+([A-Za-z\s&]+?)(?:\n|Date|Plan)",
]


def _first_match(text: str, patterns: list) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "unknown"


def extract_client_name(text: str) -> str:
    return _first_match(text, CLIENT_PATTERNS)


def extract_document_date(text: str) -> str:
    return _first_match(text, DATE_PATTERNS)


def extract_adviser(text: str) -> str:
    return _first_match(text, ADVISER_PATTERNS)


# ---------------------------------------------------------------------------
# Keyword tagging
# ---------------------------------------------------------------------------

TAG_RULES = {
    "equities":       ["equities", "shares", "asx", "stock", "holdings"],
    "retirement":     ["retirement", "retire", "superannuation", "super"],
    "risk_profile":   ["risk profile", "risk assessment", "risk tolerance"],
    "insurance":      ["insurance", "income protection", "tpd", "life cover"],
    "estate_planning":["estate", "will", "testamentary", "trust"],
    "property":       ["property", "reit", "real estate", "mortgage"],
    "fixed_income":   ["fixed income", "bonds", "bond"],
    "fees":           ["fee", "fees", "mer", "cost of advice"],
    "goals":          ["goals", "objectives", "target", "timeframe"],
}


def extract_tags(text: str) -> list:
    lowered = text.lower()
    return [tag for tag, keywords in TAG_RULES.items()
            if any(kw in lowered for kw in keywords)]


# ---------------------------------------------------------------------------
# Full text helper — flatten all pages into one string
# ---------------------------------------------------------------------------

def get_full_text(ingested: dict) -> str:
    return " ".join(page["text"] for page in ingested.get("pages", []))


# ---------------------------------------------------------------------------
# Main metadata builder
# ---------------------------------------------------------------------------

def build_metadata(ingested: dict) -> dict:
    full_text = get_full_text(ingested)

    return {
        "document_type":   classify_document_type(full_text),
        "client_name":     extract_client_name(full_text),
        "document_date":   extract_document_date(full_text),
        "adviser":         extract_adviser(full_text),
        "tags":            extract_tags(full_text),
        "file_name":       ingested["file_name"],
        "file_type":       ingested["file_type"],
        "page_count":      ingested["page_count"],
        "total_tables":    ingested.get("total_tables", 0),
        "extracted_at":    datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_metadata_tagging(processed_dir: Path) -> None:
    files = sorted(processed_dir.glob("*_ingested.json"))

    if not files:
        print(f"No ingested files found in {processed_dir}")
        return

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            ingested = json.load(f)

        metadata = build_metadata(ingested)
        ingested["metadata"] = metadata

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ingested, f, indent=2, ensure_ascii=False)

        print(f"Tagged: {file_path.name}")
        print(f"  type    : {metadata['document_type']}")
        print(f"  client  : {metadata['client_name']}")
        print(f"  date    : {metadata['document_date']}")
        print(f"  adviser : {metadata['adviser']}")
        print(f"  tags    : {', '.join(metadata['tags'])}")
        print()


if __name__ == "__main__":
    run_metadata_tagging(Path("data/processed"))
