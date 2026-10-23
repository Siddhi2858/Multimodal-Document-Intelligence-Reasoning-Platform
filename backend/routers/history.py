"""
routers/history.py
-------------------
Query history endpoint.

Routes:
  GET /api/history  → return all past questions, newest first
"""

from fastapi import APIRouter

from models.history import HistoryEntry
from data.history import get_history

router = APIRouter(tags=["History"])


@router.get("/history", response_model=list[HistoryEntry])
def list_history():
    """
    Return the full query history, newest entry first.

    The History Drawer in the frontend uses this endpoint to populate
    its list of previous questions.
    """
    return get_history()
