from dataclasses import dataclass

from app.ai.llm_service import LLMProvider
from app.schemes.models import Scheme
from app.schemes.schemas import SchemeSearchProfile


SYSTEM_PROMPT = """You are a financial literacy assistant that explains government \
scheme information to users of the Financial Compass platform.

STRICT RULES, apply these to every response:

- Use ONLY the information given to you in the CONTEXT, SCHEME DETAILS, and \
MATCH SUMMARY sections. Never introduce a fact, document, condition, or figure \
that is not explicitly present there.

- Never state or imply that the user IS eligible, WILL be approved, or is \
GUARANTEED anything. This is a potential-relevance indicator, not an eligibility \
decision.

- If the MATCH SUMMARY lists items under "needs verification," you must \
explicitly mention that official verification is required for those specific items.

- Write 2-3 plain-language sentences. No bullet points, no headers, no markdown.

- If you are unsure whether something is supported by the given information, \
omit it rather than guess.

"""


@dataclass
class ConditionSummary:
    matched: list[str]
    needs_verification: list[str]


def build_condition_summary(
    scheme: Scheme,
    profile: SchemeSearchProfile,
) -> ConditionSummary:
    """
    Deterministically compares profile fields against scheme restrictions.

    This is the 'eligibility comparison' step from the spec's pipeline —
    done in code, not by the LLM, so the LLM never has to (and never gets
    the chance to) decide what matches; it only narrates what code already decided.
    """

    matched: list[str] = []
    needs_verification: list[str] = []

    if scheme.states:
        if profile.state and profile.state in scheme.states:
            matched.append(
                f"State ({profile.state}) is within this scheme's eligible states."
            )
        else:
            needs_verification.append("State eligibility.")

    if scheme.occupations:
        if profile.occupation and profile.occupation in scheme.occupations:
            matched.append(
                f"Occupation ({profile.occupation}) matches this scheme's target occupation."
            )
        else:
            needs_verification.append("Occupation eligibility.")

    if scheme.target_groups:
        if profile.target_groups and set(profile.target_groups) & set(
            scheme.target_groups
        ):
            matched.append(
                "Self-identified group matches this scheme's target group."
            )
        else:
            needs_verification.append("Target group eligibility.")

    if scheme.min_income is not None or scheme.max_income is not None:
        if profile.monthly_income is not None:
            annual_income = profile.monthly_income * 12

            within_min = (
                scheme.min_income is None
                or annual_income >= scheme.min_income
            )

            within_max = (
                scheme.max_income is None
                or annual_income <= scheme.max_income
            )

            if within_min and within_max:
                matched.append(
                    "Reported income falls within this scheme's stated income range."
                )
            else:
                needs_verification.append("Income eligibility.")
        else:
            needs_verification.append(
                "Income eligibility (income not provided)."
            )

    return ConditionSummary(
        matched=matched,
        needs_verification=needs_verification,
    )


async def generate_scheme_explanation(
    llm: LLMProvider,
    scheme: Scheme,
    profile: SchemeSearchProfile,
    grounding_chunks: list[str],
    condition_summary: ConditionSummary,
) -> str:
    context_text = (
        "\n".join(f"- {c}" for c in grounding_chunks)
        or "(no additional document excerpts retrieved)"
    )

    user_prompt = f"""SCHEME DETAILS:
Name: {scheme.scheme_name}
Benefits: {scheme.benefits}

CONTEXT (retrieved excerpts from the scheme document):
{context_text}

MATCH SUMMARY (already determined programmatically — do not re-derive this):
Matched: {
    '; '.join(condition_summary.matched)
    or 'None determined from the information provided.'
}
Needs verification: {
    '; '.join(condition_summary.needs_verification)
    or 'None beyond the standard note below.'
}

Write a short, plain-language explanation of why this scheme may be relevant to \
the user, based only on the above. Always end by noting that the full eligibility \
conditions and required documents still need to be checked against the official source."""

    return (await llm.generate(SYSTEM_PROMPT, user_prompt)).strip()


def categorize_match(summary: ConditionSummary) -> str:
    """
    Maps a condition summary to one of the result categories.

    'Not Matched' schemes never reach this function because they are already
    excluded by the metadata filtering step.
    """

    if summary.matched and not summary.needs_verification:
        return "Likely Relevant"

    if summary.matched:
        return "Potentially Relevant — Verify Conditions"

    return "Insufficient Information"