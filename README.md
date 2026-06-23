# Financial Advisor AI Data Pipeline

A learning project that builds a document processing pipeline for a financial advisor AI agent. It reads client financial documents (PDF and Word), extracts text and tables, tags metadata, tracks data lineage, and uses the Claude API to summarise documents, answer questions, and extract structured insights.

---

## How It Works

Documents move through four stages:

```
Raw Documents → Ingestion → Metadata Tagging → Lineage Tracking → Claude Agent → Responses
```

By the time Claude receives a document, it already knows the document type, client name, and key topics — which is why the AI responses are specific rather than generic.

---

## Project Structure

```
AI Data pipeline/
├── data/
│   ├── sample_docs/        # Generated test documents (PDF + Word)
│   └── processed/          # Extracted text, metadata, and lineage (JSON)
├── pipeline/
│   ├── ingestion.py        # Extract text and tables from documents
│   ├── metadata.py         # Classify and tag each document
│   ├── lineage.py          # Audit trail — records every step applied
│   └── claude_agent.py     # Claude Q&A, summarisation, insight extraction
├── outputs/responses/      # Claude's responses saved as JSON
├── generate_samples.py     # Creates sample financial documents for testing
├── main.py                 # Run the full pipeline or query a single document
└── requirements.txt
```

---

## Setup

**1. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API key**
```bash
cp .env.example .env
```
Open `.env` and add your Anthropic API key (`sk-ant-...`).

**4. Generate sample documents**
```bash
python generate_samples.py
```

---

## Usage

| Command | What it does |
|---|---|
| `python main.py` | Run the full pipeline on all documents |
| `python main.py --doc financial_plan` | Summarise and extract insights from one document |
| `python main.py --doc risk_assessment --ask "What is the client's risk profile?"` | Ask a question |
| `python main.py --doc investment_proposal --summarise` | Summarise only |
| `python main.py --doc investment_proposal --insights` | Extract structured insights only |

---

## Dependencies

| Library | Purpose |
|---|---|
| `anthropic` | Claude API client |
| `pymupdf` | PDF text and table extraction |
| `python-docx` | Word document extraction |
| `reportlab` | Generating sample financial PDFs |
| `python-dotenv` | Loads API key from `.env` |
| `pydantic` | Typed data models |

---

## Notes

- Never commit `.env` — your API key lives there and is already excluded by `.gitignore`
- All sample documents are fictional — no real client data is used
- Each pipeline module can be run independently for testing
