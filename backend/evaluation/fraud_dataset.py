# evaluation/fraud_dataset.py

FRAUD_EVAL_CASES = [
    # (text, is_actually_scam, expected_min_risk)
    ("URGENT: Your account will be blocked within 24 hours. Share the OTP immediately.", True, "High"),
    ("Congratulations! You've won a guaranteed risk-free investment returning 50% monthly.", True, "High"),
    ("Dear customer, your KYC needs update. Click here to verify: http://192.168.1.5/kyc", True, "High"),
    ("This is RBI calling. You are under investigation. Verify via video call now.", True, "High"),
    ("Install AnyDesk so our support team can fix your account issue.", True, "High"),
    ("Pay the remaining amount to this UPI ID immediately to avoid penalty.", True, "Medium"),
    ("Your parcel is delayed, please call our toll-free number for details.", False, "Low"),
    ("Your electricity bill of Rs 1200 is due on the 5th.", False, "Low"),
    ("Hi, are we still meeting for lunch tomorrow?", False, "Low"),
    ("Your OTP for login is 4521. Do not share this with anyone.", False, "Low"),
]