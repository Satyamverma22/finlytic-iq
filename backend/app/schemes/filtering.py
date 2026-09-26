# app/schemes/filtering.py

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemes.models import Scheme
from app.schemes.schemas import SchemeSearchProfile


async def filter_schemes_by_profile(
    db: AsyncSession, profile: SchemeSearchProfile
) -> list[Scheme]:
    """
    Narrows the scheme pool using only structured facts — never semantic
    similarity. A scheme is excluded only when it has an EXPLICIT
    restriction on a dimension the user provided, and that restriction
    doesn't match. A scheme with no stated restriction on a dimension
    always passes through on that dimension, regardless of profile data.
    """
    conditions = []

    if profile.state:
        conditions.append(
            or_(Scheme.states.is_(None), Scheme.states.overlap([profile.state]))
        )

    if profile.occupation:
        conditions.append(
            or_(Scheme.occupations.is_(None), Scheme.occupations.overlap([profile.occupation]))
        )

    if profile.education_level:
        conditions.append(
            or_(
                Scheme.education_levels.is_(None),
                Scheme.education_levels.overlap([profile.education_level]),
            )
        )

    if profile.business_type:
        conditions.append(
            or_(
                Scheme.business_types.is_(None),
                Scheme.business_types.overlap([profile.business_type]),
            )
        )

    if profile.target_groups:
        conditions.append(
            or_(
                Scheme.target_groups.is_(None),
                Scheme.target_groups.overlap(profile.target_groups),
            )
        )

    if profile.monthly_income is not None:
        annual_income = profile.monthly_income * 12
        conditions.append(or_(Scheme.min_income.is_(None), Scheme.min_income <= annual_income))
        conditions.append(or_(Scheme.max_income.is_(None), Scheme.max_income >= annual_income))

    query = select(Scheme)
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    return list(result.scalars().all())