"""
PocketSmart AI — Recommendation Models
Pydantic schemas for AI-generated recommendations and history.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
import uuid


class PlannerType(str, Enum):
    home = "home"
    party = "party"
    jewelry = "jewelry"


class BudgetAllocationItem(BaseModel):
    category: str
    allocated_budget: float
    percentage: float = 0.0


class RecommendationItem(BaseModel):
    name: str
    category: str
    estimated_price: float
    platform: str = "General Market"
    reason: str = ""
    style: str = ""
    url: str = ""
    quantity: int = 1


class BudgetSummary(BaseModel):
    total_budget: float
    estimated_spend: float
    remaining: float
    within_budget: bool


class PlannerResult(BaseModel):
    summary: str
    budget_summary: BudgetSummary
    budget_allocation: List[BudgetAllocationItem]
    recommendations: List[RecommendationItem]
    ai_notes: str = ""
    planner_type: PlannerType
    # Jewelry-specific
    outfit_analysis: Optional[str] = None


class HistoryEntry(BaseModel):
    id: str
    user_id: str
    planner_type: PlannerType
    input_summary: str
    budget: float
    result: PlannerResult
    created_at: datetime


# ─── In-Memory History Store ─────────────────────────────────────────────────
_history_db: list[HistoryEntry] = []


def save_history(user_id: str, planner_type: PlannerType, input_summary: str,
                 budget: float, result: PlannerResult) -> HistoryEntry:
    entry = HistoryEntry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        planner_type=planner_type,
        input_summary=input_summary,
        budget=budget,
        result=result,
        created_at=datetime.utcnow(),
    )
    _history_db.append(entry)
    return entry


def get_user_history(user_id: str) -> list[HistoryEntry]:
    # Return most recent first, limit to 50
    user_entries = [e for e in _history_db if e.user_id == user_id]
    return sorted(user_entries, key=lambda e: e.created_at, reverse=True)[:50]


def get_history_entry(entry_id: str, user_id: str) -> Optional[HistoryEntry]:
    """Get a specific entry, only if it belongs to the user."""
    for entry in _history_db:
        if entry.id == entry_id and entry.user_id == user_id:
            return entry
    return None
