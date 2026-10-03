# evaluation/run_scheme_eval.py
import asyncio

from app.core.database import AsyncSessionLocal
from app.schemes.filtering import filter_schemes_by_profile
from app.schemes.schemas import SchemeSearchProfile
from evaluation.scheme_dataset import SCHEME_EVAL_CASES


async def main():
    tp = fp = fn = 0
    async with AsyncSessionLocal() as db:
        for profile_kwargs, expected in SCHEME_EVAL_CASES:
            profile = SchemeSearchProfile(**profile_kwargs)
            results = await filter_schemes_by_profile(db, profile)
            actual = {s.scheme_name for s in results}

            case_tp = actual & expected
            case_fp = actual - expected
            case_fn = expected - actual
            tp += len(case_tp)
            fp += len(case_fp)
            fn += len(case_fn)

            status = "OK" if actual == expected else "MISS"
            print(f"[{status}] profile={profile_kwargs}")
            print(f"       expected={expected or '(none)'}")
            print(f"       actual=  {actual or '(none)'}")

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    print(f"\nPrecision: {precision:.2f}  Recall: {recall:.2f}  TP={tp} FP={fp} FN={fn}")


if __name__ == "__main__":
    asyncio.run(main())