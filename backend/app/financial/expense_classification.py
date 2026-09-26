# app/financial/expense_classification.py

ESSENTIAL_CATEGORIES = {
    "Housing",
    "Utilities",
    "Groceries",
    "Healthcare",
    "Insurance",
    "Debt",
    "Transport",
}

DISCRETIONARY_CATEGORIES = {
    "Food",
    "Entertainment",
    "Shopping",
}


def classify_expense(category: str | None) -> str:
    """
    Returns 'essential', 'discretionary', or 'uncategorized'.
    Categories not in either set fall back to 'uncategorized' rather
    than guessing — same never-fabricate principle as the rule engine itself.
    """
    if category is None:
        return "uncategorized"
    if category in ESSENTIAL_CATEGORIES:
        return "essential"
    if category in DISCRETIONARY_CATEGORIES:
        return "discretionary"
    return "uncategorized"