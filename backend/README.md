# Folio — Backend API

FastAPI backend for the **Folio Multimodal Document Intelligence and Reasoning Platform**.

---

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the development server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs (Swagger UI) are at `http://localhost:8000/docs`.

---

## Project Structure

```
backend/
├── main.py               ← FastAPI app, CORS, router registration
├── requirements.txt      ← Python dependencies
│
├── models/               ← Pydantic data models (schemas)
│   ├── document.py       ← DocumentRecord
│   ├── page.py           ← PageRecord, PageProbabilities
│   ├── qa.py             ← AskRequest, QuestionResponse, QuestionSource
│   └── history.py        ← HistoryEntry
│
├── data/                 ← In-memory data stores
│   ├── catalogue.py      ← Document list + helpers
│   ├── pages.py          ← Page classification data
│   ├── qa_bank.py        ← Pre-written Q&A pairs + lookup logic
│   └── history.py        ← Query history store
│
└── routers/              ← API route handlers
    ├── documents.py      ← /api/documents/* endpoints
    ├── questions.py      ← /api/documents/{id}/ask endpoint
    └── history.py        ← /api/history endpoint
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/documents` | List all documents |
| `GET` | `/api/documents/{id}` | Get one document |
| `POST` | `/api/documents/upload` | Upload a PDF (simulated) |
| `GET` | `/api/documents/{id}/pages` | Get page breakdown |
| `POST` | `/api/documents/{id}/ask` | Ask a question |
| `GET` | `/api/history` | Get query history |

### Ask a question

```http
POST /api/documents/doc-1/ask
Content-Type: application/json

{
  "question": "What were the empirical results on low-contrast scanned documents?"
}
```

**Response (found)**
```json
{
  "found": true,
  "answer": "When evaluated on scanned document test sets...",
  "sources": [
    {
      "page_number": 18,
      "chunk_id": "chk-18-04",
      "snippet": "\"OCR degradation benchmarks...\"",
      "score": 0.79,
      "top_offset": 160
    }
  ]
}
```

**Response (not found)**
```json
{
  "found": false,
  "answer": "",
  "sources": []
}
```

---

## Connecting the Frontend

The Vite dev server runs on `http://localhost:5173` by default. CORS is
already configured to allow requests from that origin.

To wire the frontend to the backend, update the base URL used in the
frontend's API calls from the mock data imports to:

```
http://localhost:8000/api
```

---

## Notes

- All data is stored in memory. Restarting the server resets any uploaded
  documents or new history entries to the seed data.
- The Q&A system uses keyword matching against a pre-written bank of
  answers. Unknown questions return `{ "found": false }`.
