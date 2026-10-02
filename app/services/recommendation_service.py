"""
PocketSmart AI — Recommendation Service
Orchestrates: validation → Gemini → budget calculation → history save
"""
import logging
from typing import Optional

from app.models.recommendation import (
    PlannerResult, PlannerType, BudgetAllocationItem,
    BudgetSummary, RecommendationItem, save_history
)
from app.services import gemini_utils

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _calculate_budget_summary(budget: float, allocation: list[BudgetAllocationItem],
                               recommendations: list[RecommendationItem]) -> BudgetSummary:
    """Python calculates the budget math — never trust AI for arithmetic."""
    estimated_spend = sum(r.estimated_price * r.quantity for r in recommendations)
    # Clamp to budget if AI slightly exceeded it
    remaining = budget - estimated_spend
    return BudgetSummary(
        total_budget=budget,
        estimated_spend=round(estimated_spend, 2),
        remaining=round(remaining, 2),
        within_budget=estimated_spend <= budget * 1.05,  # 5% tolerance
    )


def _parse_allocation(raw_allocation: list, budget: float) -> list[BudgetAllocationItem]:
    items = []
    for item in raw_allocation:
        try:
            alloc = float(item.get("allocated_budget", 0))
            pct = round((alloc / budget * 100), 1) if budget > 0 else 0
            items.append(BudgetAllocationItem(
                category=str(item.get("category", "General")),
                allocated_budget=alloc,
                percentage=pct,
            ))
        except (ValueError, TypeError):
            continue
    return items


def _parse_recommendations(raw_recs: list) -> list[RecommendationItem]:
    items = []
    for item in raw_recs:
        try:
            items.append(RecommendationItem(
                name=str(item.get("name", "Item")),
                category=str(item.get("category", "General")),
                estimated_price=float(item.get("estimated_price", 0)),
                platform=str(item.get("platform", "General Market")),
                reason=str(item.get("reason", "")),
                style=str(item.get("style", "")),
                url=str(item.get("url", "")),
                quantity=int(item.get("quantity", 1)),
            ))
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed recommendation item: {e}")
            continue
    return items


def process_home_planner(data: dict, user_id: str) -> PlannerResult:
    """Full home planner pipeline."""
    budget = float(data["budget"])
    raw = gemini_utils.generate_home_recommendations(data)

    allocation = _parse_allocation(raw.get("budget_allocation", []), budget)
    recommendations = _parse_recommendations(raw.get("recommendations", []))
    budget_summary = _calculate_budget_summary(budget, allocation, recommendations)

    result = PlannerResult(
        summary=raw.get("summary", "Home interior plan generated."),
        budget_summary=budget_summary,
        budget_allocation=allocation,
        recommendations=recommendations,
        ai_notes=raw.get("ai_notes", ""),
        planner_type=PlannerType.home,
    )

    # Save to history
    rooms = ", ".join(data.get("rooms", ["Living Room"]))
    save_history(
        user_id=user_id,
        planner_type=PlannerType.home,
        input_summary=f"Home ({data.get('style', 'modern')}) - {rooms}",
        budget=budget,
        result=result,
    )
    return result


def process_party_planner(data: dict, user_id: str) -> PlannerResult:
    """Full party planner pipeline."""
    budget = float(data["budget"])
    raw = gemini_utils.generate_party_recommendations(data)

    allocation = _parse_allocation(raw.get("budget_allocation", []), budget)
    recommendations = _parse_recommendations(raw.get("recommendations", []))
    budget_summary = _calculate_budget_summary(budget, allocation, recommendations)

    result = PlannerResult(
        summary=raw.get("summary", "Event plan generated."),
        budget_summary=budget_summary,
        budget_allocation=allocation,
        recommendations=recommendations,
        ai_notes=raw.get("ai_notes", ""),
        planner_type=PlannerType.party,
    )

    save_history(
        user_id=user_id,
        planner_type=PlannerType.party,
        input_summary=f"{data.get('event_type', 'Event')} - {data.get('guest_count', 0)} guests",
        budget=budget,
        result=result,
    )
    return result


def process_jewelry_planner(data: dict, user_id: str,
                             image_bytes: Optional[bytes] = None,
                             image_mime: Optional[str] = None) -> PlannerResult:
    """Full jewelry planner pipeline, with optional image."""
    budget = float(data["budget"])
    raw = gemini_utils.generate_jewelry_recommendations(
        data, image_bytes=image_bytes, image_mime=image_mime
    )

    allocation = _parse_allocation(raw.get("budget_allocation", []), budget)
    recommendations = _parse_recommendations(raw.get("recommendations", []))
    budget_summary = _calculate_budget_summary(budget, allocation, recommendations)

    result = PlannerResult(
        summary=raw.get("summary", "Jewelry plan generated."),
        budget_summary=budget_summary,
        budget_allocation=allocation,
        recommendations=recommendations,
        ai_notes=raw.get("ai_notes", ""),
        planner_type=PlannerType.jewelry,
        outfit_analysis=raw.get("outfit_analysis"),
    )

    jewelry_types = ", ".join(data.get("jewelry_types", ["jewelry"]))
    save_history(
        user_id=user_id,
        planner_type=PlannerType.jewelry,
        input_summary=f"{data.get('occasion', 'Occasion')} - {jewelry_types}",
        budget=budget,
        result=result,
    )
    return result


def validate_image(content_type: str, size: int) -> Optional[str]:
    """Return error message if image is invalid, or None if valid."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        return f"Invalid image type '{content_type}'. Allowed: JPG, PNG, WEBP."
    if size > MAX_IMAGE_SIZE_BYTES:
        return f"Image too large ({size // 1024}KB). Maximum: 5MB."
    return None
