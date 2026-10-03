# evaluation/scheme_dataset.py
from decimal import Decimal

# (profile_kwargs, expected_scheme_names)
SCHEME_EVAL_CASES = [
    (
        {"state": "Haryana", "target_groups": ["student"], "monthly_income": Decimal("20000")},
        {"State Student Scholarship Program (Prototype)"},
    ),
    (
        {"target_groups": ["woman"], "business_type": "new business"},
        {"Women Entrepreneur Startup Grant (Prototype)"},
    ),
    (
        {"target_groups": ["small business owner"], "business_type": "MSME"},
        {"MSME Collateral-Free Loan Scheme (Prototype)"},
    ),
    (
        {},
        {
            "State Student Scholarship Program (Prototype)",
            "Women Entrepreneur Startup Grant (Prototype)",
            "MSME Collateral-Free Loan Scheme (Prototype)",
        },
    ),
    (
        # student, but income over the scholarship's cap — should match nothing
        {"state": "Haryana", "target_groups": ["student"], "monthly_income": Decimal("50000")},
        set(),
    ),
    (
        # wrong state for the scholarship, no other scheme targets students
        {"state": "Kerala", "target_groups": ["student"], "monthly_income": Decimal("20000")},
        set(),
    ),
]