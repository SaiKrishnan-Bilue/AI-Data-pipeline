# Financial Advisor AI Data Pipeline

A learning project that builds a document processing pipeline for a financial advisor AI agent. It reads client financial documents (PDF and Word), extracts and tags the content, tracks data lineage, and uses the Claude API to answer questions, summarise, and extract insights.

---

## What This Pipeline Does

1. Generates realistic sample financial documents (PDFs and Word docs) for testing
2. Ingests those documents and extracts raw text
3. Tags each document with metadata (file type, page count, timestamps, etc.)
4. Tracks data lineage — a record of where each piece of data came from and every transformation applied to it
5. Sends extracted content to Claude to answer questions, produce summaries, and surface insights

---

## Project Structure

```
AI Data pipeline/
├── data/
│   ├── raw/              # Input documents (PDF and Word)
│   ├── processed/        # Extracted text and metadata (JSON)
│   └── sample_docs/      # Generated test documents
├── pipeline/             # All pipeline modules (built step by step)
├── outputs/
│   └── responses/        # Claude's answers, summaries, and insights
├── tests/                # Test scripts for each pipeline stage
├── .env                  # Your API key (never commit this)
├── .env.example          # Template for .env
├── requirements.txt      # Python dependencies
└── main.py               # Pipeline entry point (added later)
```

---

## Prerequisites

- **Python 3.10 or higher**
- **An Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)
- **pip** for installing dependencies

---

## Setup

### 1. Clone or download the project

```bash
cd "AI Data pipeline"
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your real key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| `anthropic` | >=0.40.0 | Claude API client |
| `pymupdf` | >=1.24.0 | PDF text extraction |
| `python-docx` | >=1.1.0 | Word document text extraction |
| `reportlab` | >=4.2.0 | Generating sample financial PDFs |
| `python-dotenv` | >=1.0.0 | Loading API key from `.env` |
| `pydantic` | >=2.7.0 | Typed data models for metadata and lineage |

---

## Build Steps

This project is built incrementally — one step at a time.

| Step | What gets built |
|---|---|
| 1 | Sample document generation (PDF + Word test data) |
| 2 | Document ingestion — extract raw text from PDFs and Word files |
| 3 | Metadata tagging — attach structured info to each document |
| 4 | Data lineage tracking — log every transformation |
| 5 | Claude integration — Q&A, summarisation, insight extraction |
| 6 | Main entry point — wire the full pipeline together |

---

## Notes

- Never commit your `.env` file — it contains your private API key
- All test documents are synthetic and contain no real client data
- Each pipeline module is independent and can be tested in isolation
