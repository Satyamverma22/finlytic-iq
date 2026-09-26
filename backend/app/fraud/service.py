# app/fraud/service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import get_llm_provider
from app.fraud.classification import classify_fraud
from app.fraud.models import FraudScan
from app.fraud.risk_aggregation import aggregate_risk
from app.fraud.rule_engine import extract_urls, run_fraud_rules
from app.fraud.schemas import FraudAnalyseTextRequest


async def analyse_text(
    db: AsyncSession, user_id, payload: FraudAnalyseTextRequest
) -> FraudScan:
    signals, score = run_fraud_rules(payload.text)
    risk_level = aggregate_risk(signals, score)
    urls = extract_urls(payload.text)

    llm = get_llm_provider()
    category, explanation, action = await classify_fraud(
        llm, payload.text, signals, risk_level, urls
    )

    scan = FraudScan(
        user_id=user_id,
        input_type=payload.input_type,
        raw_input_text=payload.text,
        detected_signals=signals,
        risk_score=score,
        risk_level=risk_level,
        scam_category=category,
        explanation=explanation,
        recommended_action=action,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan