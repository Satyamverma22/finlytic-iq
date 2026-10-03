# evaluation/run_fraud_eval.py

from app.fraud.rule_engine import run_fraud_rules
from app.fraud.risk_aggregation import aggregate_risk
from evaluation.fraud_dataset import FRAUD_EVAL_CASES

RISK_RANK = {"Low": 0, "Medium": 1, "High": 2}

def main():
    tp = fp = tn = fn = 0
    for text, is_scam, expected_min_risk in FRAUD_EVAL_CASES:
        signals, score = run_fraud_rules(text)
        risk = aggregate_risk(signals, score)
        flagged = RISK_RANK[risk] >= 1  # Medium or High counts as "flagged"

        if is_scam and flagged:
            tp += 1
        elif is_scam and not flagged:
            fn += 1
        elif not is_scam and flagged:
            fp += 1
        else:
            tn += 1

        match = "OK" if (RISK_RANK[risk] >= RISK_RANK[expected_min_risk]) == is_scam or not is_scam else "MISS"
        print(f"[{match}] expected>={expected_min_risk:6} got={risk:6} scam={is_scam!s:5} | {text[:60]}")

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    fpr = fp / (fp + tn) if (fp + tn) else float("nan")

    print(f"\nPrecision: {precision:.2f}  Recall: {recall:.2f}  False positive rate: {fpr:.2f}")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")

if __name__ == "__main__":
    main()