# app/schemes/seed_runner.py

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.schemes.models import Scheme
from app.schemes.document_models import DocumentChunk
from app.schemes.seed_data import SEED_SCHEMES, SYNTHETIC_SOURCE_LABEL


def _build_chunks_for_scheme(scheme_data: dict) -> list[dict]:
    """
    Splits a scheme's descriptive text into labeled chunks, ready for
    embedding in Step 5. Not embedded yet — embedding stays None here.
    """
    chunks = []
    chunks.append({"content": scheme_data["benefits"], "source_section": "Benefits"})
    chunks.append({
        "content": " ".join(scheme_data["eligibility_conditions"]),
        "source_section": "Eligibility",
    })
    if scheme_data.get("required_documents"):
        chunks.append({
            "content": "Required documents: " + ", ".join(scheme_data["required_documents"]),
            "source_section": "Required Documents",
        })
    if scheme_data.get("application_process"):
        chunks.append({
            "content": scheme_data["application_process"],
            "source_section": "Application Process",
        })
    return chunks


async def seed_schemes() -> None:
    async with AsyncSessionLocal() as db:
        for scheme_data in SEED_SCHEMES:
            existing = await db.execute(
                select(Scheme).where(Scheme.scheme_name == scheme_data["scheme_name"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"Skipping (already seeded): {scheme_data['scheme_name']}")
                continue

            scheme = Scheme(
                scheme_name=scheme_data["scheme_name"],
                scope=scheme_data["scope"],
                states=scheme_data["states"],
                target_groups=scheme_data["target_groups"],
                occupations=scheme_data["occupations"],
                education_levels=scheme_data["education_levels"],
                business_types=scheme_data["business_types"],
                min_income=scheme_data["min_income"],
                max_income=scheme_data["max_income"],
                benefits=scheme_data["benefits"],
                eligibility_conditions=scheme_data["eligibility_conditions"],
                required_documents=scheme_data["required_documents"],
                application_process=scheme_data["application_process"],
                official_url=scheme_data["official_url"],
                department=scheme_data["department"],
                source_document=SYNTHETIC_SOURCE_LABEL,
                last_verified_date=scheme_data["last_verified_date"],
            )
            db.add(scheme)
            await db.flush()  # assigns scheme.id without committing yet

            for i, chunk_data in enumerate(_build_chunks_for_scheme(scheme_data)):
                db.add(
                    DocumentChunk(
                        scheme_id=scheme.id,
                        chunk_index=i,
                        content=chunk_data["content"],
                        source_section=chunk_data["source_section"],
                        embedding=None,  # Step 5 fills this in
                    )
                )

            print(f"Seeded: {scheme_data['scheme_name']}")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_schemes())