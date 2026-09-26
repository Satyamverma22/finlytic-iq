# app/schemes/match_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import get_llm_provider
from app.schemes.explanation import build_condition_summary, categorize_match, generate_scheme_explanation
from app.schemes.filtering import filter_schemes_by_profile
from app.schemes.schemas import SchemeMatchRequest, SchemeMatchResult
from app.schemes.vector_search import search_chunks

DEFAULT_QUERY = "government schemes and benefits I may be eligible for"


async def match_schemes(db: AsyncSession, payload: SchemeMatchRequest) -> list[SchemeMatchResult]:
    candidates = await filter_schemes_by_profile(db, payload)
    if not candidates:
        return []

    query_text = payload.query or DEFAULT_QUERY
    candidate_ids = [s.id for s in candidates]
    chunk_results = await search_chunks(db, query_text, candidate_ids, top_k=15)

    # group retrieved chunks by scheme, preserving best-match order per scheme
    chunks_by_scheme: dict = {}
    for chunk, distance in chunk_results:
        chunks_by_scheme.setdefault(chunk.scheme_id, []).append(chunk.content)

    llm = get_llm_provider()
    results: list[SchemeMatchResult] = []

    for scheme in candidates:
        grounding = chunks_by_scheme.get(scheme.id, [])
        summary = build_condition_summary(scheme, payload)
        explanation = await generate_scheme_explanation(llm, scheme, payload, grounding, summary)

        results.append(
            SchemeMatchResult(
                scheme_id=scheme.id,
                scheme_name=scheme.scheme_name,
                category=categorize_match(summary),
                matched=summary.matched,
                needs_verification=summary.needs_verification,
                explanation=explanation,
                benefits=scheme.benefits,
                required_documents=scheme.required_documents,
                official_url=scheme.official_url,
                department=scheme.department,
                last_verified_date=scheme.last_verified_date,
            )
        )

    results.sort(key=lambda r: {"Likely Relevant": 0, "Potentially Relevant — Verify Conditions": 1, "Insufficient Information": 2}[r.category])
    return results