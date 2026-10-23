"""
Folio Backend — FastAPI Application
====================================
This is the main entry point for the Folio backend server.

Endpoints provided:
  GET  /                          → Health check
  GET  /api/documents             → List all documents
  GET  /api/documents/{id}        → Get one document by ID
  POST /api/documents/upload      → Simulate a PDF upload
  GET  /api/documents/{id}/pages  → Get page-level breakdown for a document
  POST /api/documents/{id}/ask    → Ask a question about a document
  GET  /api/history               → Get past query history

Run with:
  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import documents, questions, history

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Folio — Document Intelligence API",
    description=(
        "Backend for the Folio Multimodal Document Intelligence and "
        "Reasoning Platform. Provides document management, page-level "
        "classification data, and AI-style question answering backed by "
        "verified page citations."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server (localhost:5173) to talk to this API
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(documents.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(history.router, prefix="/api")


# ---------------------------------------------------------------------------
# Root health-check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "Folio Document Intelligence API"}
