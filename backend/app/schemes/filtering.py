from sqlalchemy import select, and_, or_, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemes.models import Scheme
from app.schemes.schemas import SchemeSearchProfile


def _ci_array_overlap(column, values: list[str]):
    lowered = [v.lower() for v in values]

    elem = func.unnest(column).column_valued("elem")

    return exists(
        select(1).where(func.lower(elem).in_(lowered))
    )


async def filter_schemes_by_profile(
    db: AsyncSession,
    profile: SchemeSearchProfile,
) -> list[Scheme]:

    conditions = []

    # Normalize user input
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
                _ci_array_overlap(
                    Scheme.occupations,
                    [occupation],
                ),
            )
        )

    # Education level filter
    if education_level:
        conditions.append(
            or_(
                Scheme.education_levels.is_(None),
                _ci_array_overlap(
                    Scheme.education_levels,
                    [education_level],
                ),
            )
        )

    # Business type filter
    if business_type:
        conditions.append(
            or_(
                Scheme.business_types.is_(None),
                _ci_array_overlap(
                    Scheme.business_types,
                    [business_type],
                ),
            )
        )

    # Target group filter
    if target_groups:
        conditions.append(
            or_(
                Scheme.target_groups.is_(None),
                _ci_array_overlap(
                    Scheme.target_groups,
                    target_groups,
                ),
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