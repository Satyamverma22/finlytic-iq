import asyncio

from app.consent.service import has_active_consent
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        result = await has_active_consent(
            db,
            "528edbef-f8f5-4e6c-a3d9-fd9389f5ab78",
            "financial_analysis",
        )

        print("HAS ACTIVE CONSENT:", result)


asyncio.run(main())