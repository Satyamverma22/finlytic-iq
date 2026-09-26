# app/copilot/tools.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.credit.schemas import ScenarioCreate
from app.credit.service import build_and_save_scenario
from app.credit.service import ProfileNotSetError as CreditProfileNotSetError
from app.financial.health_indicator import build_health_indicator
from app.financial.metrics_service import ProfileNotSetError, compute_metrics
from app.fraud.schemas import FraudAnalyseTextRequest
from app.fraud.service import analyse_text
from app.schemes.match_service import match_schemes
from app.schemes.schemas import SchemeMatchRequest


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON-schema shape, provider-neutral
    executor: Callable[..., Awaitable[dict]]  # always (db, user_id, **kwargs) -> dict


# ---------------------------------------------------------------------------
# Executors — every one of these is a thin wrapper around an ALREADY-BUILT,
# ALREADY-TESTED service function. No new business logic lives here. Each
# executor's signature is ALWAYS (db, user_id, **kwargs) — user_id comes from
# the authenticated request context (Step 2/7 will wire this), NEVER from
# the LLM's tool-call arguments. This is non-negotiable: an LLM that could
# supply its own user_id would let a cleverly-worded prompt read another
# user's financial data. The tool schemas below deliberately do not expose
# user_id as a parameter the model can set at all.
# ---------------------------------------------------------------------------

async def tool_get_financial_health(
    db: AsyncSession, user_id, year: int | None = None, month: int | None = None
) -> dict:
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month

    try:
        result = await compute_metrics(db, user_id, year, month)
    except ProfileNotSetError:
        return {"error": "No financial profile set up yet. Ask the user to set up their income and savings first."}

    indicator = build_health_indicator(result)
    return {
        "period": f"{year}-{month:02d}",
        "monthly_income": str(result.monthly_income),
        "monthly_expenses": str(result.monthly_expenses),
        "savings_ratio": f"{result.savings_ratio:.1%}",
        "dti": f"{result.dti:.1%}",
        "emergency_coverage_months": (
            f"{result.emergency_coverage_months:.1f}"
            if result.emergency_coverage_months is not None else None
        ),
        "category": indicator.category,
        "positive_factors": indicator.positive_factors,
        "risk_factors": indicator.risk_factors,
        "next_steps": indicator.next_steps,
        "data_limitations": indicator.data_limitations,
    }


async def tool_simulate_loan(
    db: AsyncSession, user_id, label: str,
    proposed_amount: float, annual_interest_rate: float, tenure_months: int,
) -> dict:
    payload = ScenarioCreate(
        label=label,
        proposed_amount=Decimal(str(proposed_amount)),
        annual_interest_rate=Decimal(str(annual_interest_rate)),
        tenure_months=tenure_months,
    )
    today = date.today()
    try:
        scenario, risk_category, risk_factors = await build_and_save_scenario(
            db, user_id, payload, today.year, today.month
        )
    except CreditProfileNotSetError:
        return {"error": "No financial profile set up yet. Ask the user to set up their income first."}

    return {
        "label": scenario.label,
        "estimated_emi": str(scenario.estimated_emi),
        "total_repayment": str(scenario.total_repayment),
        "total_interest": str(scenario.total_interest),
        "resulting_dti": f"{scenario.resulting_dti:.1%}",
        "remaining_cash_flow": str(scenario.remaining_cash_flow),
        "risk_category": risk_category,
        "risk_factors": risk_factors,
    }


async def tool_match_schemes(
    db: AsyncSession, user_id,
    state: str | None = None, occupation: str | None = None,
    education_level: str | None = None, business_type: str | None = None,
    monthly_income: float | None = None, target_groups: list[str] | None = None,
    query: str | None = None,
) -> dict:
    payload = SchemeMatchRequest(
        state=state, occupation=occupation, education_level=education_level,
        business_type=business_type,
        monthly_income=Decimal(str(monthly_income)) if monthly_income is not None else None,
        target_groups=target_groups, query=query,
    )
    results = await match_schemes(db, payload)
    return {
        "candidate_count": len(results),
        "results": [
            {
                "scheme_name": r.scheme_name,
                "category": r.category,
                "explanation": r.explanation,
                "official_url": r.official_url,
                "last_verified_date": str(r.last_verified_date),
            }
            for r in results
        ],
    }


async def tool_analyse_fraud_text(db: AsyncSession, user_id, input_type: str, text: str) -> dict:
    payload = FraudAnalyseTextRequest(input_type=input_type, text=text)
    scan = await analyse_text(db, user_id, payload)
    return {
        "risk_level": scan.risk_level,
        "detected_signals": scan.detected_signals,
        "scam_category": scan.scam_category,
        "explanation": scan.explanation,
        "recommended_action": scan.recommended_action,
    }


# ---------------------------------------------------------------------------
# Tool registry — the schemas here are what gets shown to the LLM so it
# knows what tools exist and what arguments each expects. Plain JSON-schema
# dicts, not Gemini-specific objects — Step 3 adapts these into whatever
# shape the concrete provider's SDK requires, keeping this file itself
# provider-neutral, same principle as embedding_service.py / llm_service.py.
# ---------------------------------------------------------------------------

TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_financial_health",
        description=(
            "Get the user's financial health report for a given month: income, "
            "expenses, savings ratio, debt-to-income ratio, emergency fund coverage, "
            "and an explained health category with positive/risk factors."
        ),
        parameters={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year, e.g. 2026. Defaults to current month if omitted."},
                "month": {"type": "integer", "description": "Month 1-12. Defaults to current month if omitted."},
            },
            "required": [],
        },
        executor=tool_get_financial_health,
    ),
    ToolDefinition(
        name="simulate_loan",
        description=(
            "Simulate taking a new loan and see its impact: estimated EMI, total "
            "interest, resulting debt-to-income ratio, remaining monthly cash flow, "
            "and a risk assessment. Saves the scenario to the user's history."
        ),
        parameters={
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "A short name for this scenario, e.g. 'New Car Loan'."},
                "proposed_amount": {"type": "number", "description": "The loan principal amount."},
                "annual_interest_rate": {"type": "number", "description": "Annual interest rate as a percentage, e.g. 9.5."},
                "tenure_months": {"type": "integer", "description": "Loan tenure in months."},
            },
            "required": ["label", "proposed_amount", "annual_interest_rate", "tenure_months"],
        },
        executor=tool_simulate_loan,
    ),
    ToolDefinition(
        name="match_schemes",
        description=(
            "Find government schemes that may be relevant to the user, based on "
            "their profile (state, occupation, income, etc.) and an optional "
            "natural-language query about what they're looking for."
        ),
        parameters={
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "occupation": {"type": "string"},
                "education_level": {"type": "string"},
                "business_type": {"type": "string"},
                "monthly_income": {"type": "number"},
                "target_groups": {"type": "array", "items": {"type": "string"}},
                "query": {"type": "string", "description": "What the user is looking for, in their own words."},
            },
            "required": [],
        },
        executor=tool_match_schemes,
    ),
    ToolDefinition(
        name="analyse_fraud_text",
        description=(
            "Analyse a message (SMS, email, WhatsApp, etc.) the user received for "
            "fraud/scam warning signs. Returns a risk level and evidence-based explanation."
        ),
        parameters={
            "type": "object",
            "properties": {
                "input_type": {
                    "type": "string",
                    "enum": ["sms", "email", "whatsapp", "url", "upi_id", "investment_offer", "call_transcript", "payment_request"],
                },
                "text": {"type": "string", "description": "The message text to analyse."},
            },
            "required": ["input_type", "text"],
        },
        executor=tool_analyse_fraud_text,
    ),
]