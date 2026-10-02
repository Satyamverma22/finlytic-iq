from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemes.models import Scheme
from app.schemes.schemas import SchemeSearchProfile


async def filter_schemes_by_profile(
    db: AsyncSession,
    profile: SchemeSearchProfile,
) -> list[Scheme]:

    conditions = []

    # Normalize user input to match the stored seed-data format.
    state = profile.state.title() if profile.state else None

    occupation = (
        profile.occupation.lower()
        if profile.occupation
        else None
    )

    education_level = (
        profile.education_level.lower()
        if profile.education_level
        else None
    )

    business_type = (
        profile.business_type.lower()
        if profile.business_type
        else None
    )

    target_groups = (
        [value.lower() for value in profile.target_groups]
        if profile.target_groups
        else None
    )

    # State filter
    if state:
        conditions.append(
            or_(
                Scheme.states.is_(None),
                Scheme.states.overlap([state]),
            )
        )

    # Occupation filter
    if occupation:
        conditions.append(
            or_(
                Scheme.occupations.is_(None),
                Scheme.occupations.overlap([occupation]),
            )
        )

    # Education level filter
    if education_level:
        conditions.append(
            or_(
                Scheme.education_levels.is_(None),
                Scheme.education_levels.overlap([education_level]),
            )
        )

    # Business type filter
    if business_type:
        conditions.append(
            or_(
                Scheme.business_types.is_(None),
                Scheme.business_types.overlap([business_type]),
            )
        )

    # Target group filter
    if target_groups:
        conditions.append(
            or_(
                Scheme.target_groups.is_(None),
                Scheme.target_groups.overlap(target_groups),
            )
        )

    # Monthly income filter
    if profile.monthly_income is not None:
        annual_income = profile.monthly_income * 12

        conditions.append(
            or_(
                Scheme.min_income.is_(None),
                Scheme.min_income <= annual_income,
            )
        )

        conditions.append(
            or_(
                Scheme.max_income.is_(None),
                Scheme.max_income >= annual_income,
            )
        )

    # Build query
    query = select(Scheme)

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)

    return list(result.scalars().all())