"""Deterministic tools for the fictional procurement workflow."""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from .retrieval import read_document

# Quotes and these structured records intentionally agree; test them when editing.
CATALOG = {
    "atlas": {"name": "Atlas", "monthly_inr": 900, "setup_inr": 20000, "minimum_seats": 10},
    "beacon": {"name": "Beacon", "monthly_inr": 750, "setup_inr": 35000, "minimum_seats": 20},
    "cedar": {"name": "Cedar", "monthly_inr": 1100, "setup_inr": 10000, "minimum_seats": 5},
}


def get_vendor_catalog() -> dict:
    """Return fictional vendor prices for calculations, not compliance evidence."""
    return {"currency": "INR", "tax": "Excluded", "vendors": CATALOG}


def calculate_quote(vendor: str, seats: int, months: int, budget_inr: float) -> dict:
    """Calculate subscription plus setup cost and compare it with a budget.

    Args:
        vendor: Vendor ID from the catalog: atlas, beacon, or cedar.
        seats: Positive integer number of seats requested.
        months: Positive integer subscription duration in months.
        budget_inr: Nonnegative budget in INR, excluding tax.
    """
    record = CATALOG.get(vendor.lower().strip())
    if record is None:
        return {"status": "error", "message": "Unknown vendor; use get_vendor_catalog."}
    try:
        budget = Decimal(str(budget_inr))
    except InvalidOperation:
        return {"status": "error", "message": "Budget must be a finite nonnegative number."}
    if not budget.is_finite() or budget < 0:
        return {"status": "error", "message": "Budget must be a finite nonnegative number."}
    if isinstance(seats, bool) or isinstance(months, bool) or not isinstance(seats, int) or not isinstance(months, int) or seats < 1 or months < 1:
        return {"status": "error", "message": "Seats and months must be positive integers."}
    billed_seats = max(seats, record["minimum_seats"])
    subscription = Decimal(billed_seats * months * record["monthly_inr"])
    total = subscription + Decimal(record["setup_inr"])
    money = lambda value: str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"status": "success", "vendor": record["name"], "requested_seats": seats,
            "billed_seats": billed_seats, "months": months, "currency": "INR",
            "subscription_inr": money(subscription), "setup_inr": money(Decimal(record["setup_inr"])),
            "total_inr": money(total), "budget_inr": money(budget),
            "remaining_budget_inr": money(budget - total), "within_budget": total <= budget,
            "tax": "Excluded", "formula": "max(requested seats, minimum seats) × monthly seat price × months + setup"}


def validate_citations(answer: str) -> dict:
    """Check whether filename/line citations exist, not whether they support claims.

    Args:
        answer: Draft text containing citations like [procurement.md:L1-L15].
    """
    citations = re.findall(r"\[([^\[\]\n:]+):L(\d+)-L(\d+)\]", answer)
    checked = []
    for source, start, end in dict.fromkeys(citations):
        passage = read_document(source, int(start), int(end))
        valid = passage.get("status") == "success" and passage.get("end_line") == int(end)
        checked.append({"citation": f"[{source}:L{start}-L{end}]", "valid": valid,
                        "content": passage.get("content", "") if valid else ""})
    return {"status": "success", "citation_count": len(checked),
            "all_valid": bool(checked) and all(item["valid"] for item in checked),
            "citations": checked,
            "limitation": "Checks source existence and line ranges only; reviewer must check claim support and coverage."}
