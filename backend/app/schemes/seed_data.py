# app/schemes/seed_data.py
"""
Synthetic, clearly-labeled seed data for the Scheme Finder prototype.
These are NOT real government schemes — names, figures, and URLs are
illustrative only. Before any real deployment, every record must be
replaced with verified data from actual official sources, per the
spec's "never scrape/fabricate scheme information" rule.
"""

from datetime import date
from decimal import Decimal

SYNTHETIC_SOURCE_LABEL = "Synthetic prototype dataset — not an official record"
PLACEHOLDER_URL_BASE = "https://example-schemes.invalid"

SEED_SCHEMES = [
    {
        "scheme_name": "State Student Scholarship Program (Prototype)",
        "scope": "state",
        "states": ["Haryana", "Punjab"],
        "target_groups": ["student"],
        "occupations": None,
        "education_levels": ["undergraduate", "postgraduate"],
        "business_types": None,
        "min_income": None,
        "max_income": Decimal("300000"),
        "benefits": (
            "Provides an annual tuition subsidy for eligible students enrolled in "
            "recognized undergraduate or postgraduate programs, intended to reduce "
            "the financial burden of tuition fees."
        ),
        "eligibility_conditions": [
            "Applicant must be a current student in an undergraduate or postgraduate program.",
            "Applicant's family income must not exceed the stated income threshold.",
            "Applicant must be a resident of an eligible state.",
        ],
        "required_documents": [
            "Domicile certificate",
            "Income certificate",
            "Proof of current enrollment",
        ],
        "application_process": (
            "Applications are typically submitted through the state education "
            "department's portal during the designated application window each year."
        ),
        "official_url": f"{PLACEHOLDER_URL_BASE}/student-scholarship",
        "department": "Prototype State Education Department",
        "last_verified_date": date(2026, 1, 1),
    },
    {
        "scheme_name": "Women Entrepreneur Startup Grant (Prototype)",
        "scope": "national",
        "states": None,
        "target_groups": ["woman", "entrepreneur", "first-time business owner"],
        "occupations": None,
        "education_levels": None,
        "business_types": ["new business", "startup"],
        "min_income": None,
        "max_income": None,
        "benefits": (
            "Offers a one-time grant to support women launching a new small business, "
            "intended to help cover initial setup costs."
        ),
        "eligibility_conditions": [
            "Applicant must identify as a woman.",
            "The business must be newly established, generally within the last two years.",
            "The applicant must hold majority ownership of the business.",
        ],
        "required_documents": [
            "Business registration certificate",
            "Identity proof",
            "Business plan document",
        ],
        "application_process": (
            "Applications are submitted online along with a brief business plan; "
            "shortlisted applicants may be asked for a follow-up review."
        ),
        "official_url": f"{PLACEHOLDER_URL_BASE}/women-entrepreneur-grant",
        "department": "Prototype Ministry of MSME",
        "last_verified_date": date(2026, 1, 1),
    },
    {
        "scheme_name": "MSME Collateral-Free Loan Scheme (Prototype)",
        "scope": "national",
        "states": None,
        "target_groups": ["small business owner"],
        "occupations": None,
        "education_levels": None,
        "business_types": ["MSME", "small business"],
        "min_income": None,
        "max_income": None,
        "benefits": (
            "Facilitates access to collateral-free credit for registered MSMEs, "
            "intended to support working-capital and expansion needs."
        ),
        "eligibility_conditions": [
            "The business must be a registered MSME (Micro, Small, or Medium Enterprise).",
            "The business must have been operational for at least one year.",
            "The business must not have existing loan defaults on record.",
        ],
        "required_documents": [
            "MSME registration certificate",
            "Business financial statements",
            "GST filing records",
        ],
        "application_process": (
            "Applications are submitted through empanelled lending institutions "
            "participating in the scheme."
        ),
        "official_url": f"{PLACEHOLDER_URL_BASE}/msme-collateral-free-loan",
        "department": "Prototype Ministry of MSME",
        "last_verified_date": date(2026, 1, 1),
    },
]