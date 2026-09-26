# app/transactions/categorization.py

import re
from dataclasses import dataclass


@dataclass
class CategoryRule:
    pattern: re.Pattern
    category: str
    subcategory: str


def _rule(keyword: str, category: str, subcategory: str) -> CategoryRule:
    # word-boundary, case-insensitive match on the raw description
    return CategoryRule(
        pattern=re.compile(re.escape(keyword), re.IGNORECASE),
        category=category,
        subcategory=subcategory,
    )


# Ordered deliberately: more specific patterns before more general ones.
CATEGORY_RULES: list[CategoryRule] = [
    _rule("SWIGGY", "Food", "Food Delivery"),
    _rule("ZOMATO", "Food", "Food Delivery"),
    _rule("UBER", "Transport", "Ride Hailing"),
    _rule("OLA", "Transport", "Ride Hailing"),
    _rule("IRCTC", "Transport", "Train Travel"),
    _rule("NETFLIX", "Entertainment", "Subscription"),
    _rule("SPOTIFY", "Entertainment", "Subscription"),
    _rule("AMAZON PRIME", "Entertainment", "Subscription"),
    _rule("AMAZON", "Shopping", "Online Shopping"),
    _rule("FLIPKART", "Shopping", "Online Shopping"),
    _rule("BIGBASKET", "Groceries", "Online Groceries"),
    _rule("BLINKIT", "Groceries", "Online Groceries"),
    _rule("ZEPTO", "Groceries", "Online Groceries"),
    _rule("ELECTRICITY", "Utilities", "Electricity"),
    _rule("BROADBAND", "Utilities", "Internet"),
    _rule("AIRTEL", "Utilities", "Mobile/Internet"),
    _rule("JIO", "Utilities", "Mobile/Internet"),
    _rule("RENT", "Housing", "Rent"),
    _rule("SALARY", "Income", "Salary"),
    _rule("EMI", "Debt", "Loan EMI"),
    _rule("INSURANCE", "Insurance", "Premium"),
    _rule("HOSPITAL", "Healthcare", "Medical"),
    _rule("PHARMACY", "Healthcare", "Medicine"),
    _rule("APOLLO", "Healthcare", "Medical"),
]


def categorize_transaction(description: str) -> tuple[str | None, str | None, float | None]:
    """
    Returns (category, subcategory, confidence).
    (None, None, None) if no rule matches — leaves the transaction
    for ML categorisation later, rather than forcing a guess now.
    """
    for rule in CATEGORY_RULES:
        if rule.pattern.search(description):
            return rule.category, rule.subcategory, 1.0
    return None, None, None