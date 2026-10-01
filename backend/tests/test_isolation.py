# tests/test_isolation.py

from app.core import redis_client
from app.core import redis_client
from app.core import redis_client
import pytest

pytestmark = pytest.mark.asyncio


async def test_unauthenticated_access_denied(client):
    for method, path in [
        ("get", "/api/financial/health"),
        ("get", "/api/transactions"),
        ("get", "/api/credit-scenarios"),
        ("get", "/api/fraud/scans"),
        ("post", "/api/schemes/match"),
        ("post", "/api/copilot/chat"),
        ("get", "/api/consents"),
    ]:
        if method == "post":
            res = await client.post(path, json={})
        else:
            res = await client.get(path)

        assert res.status_code == 401, f"{path} did not require auth"


async def test_bad_token_rejected(client):
    res = await client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


async def test_cross_user_financial_profile_isolation(client, user_a, user_b):
    await client.put("/api/financial/profile", json={
        "monthly_income": 60000, "liquid_savings": 30000, "emergency_fund_target_months": 3,
    }, headers=user_a)

    res_a = await client.get("/api/financial/profile", headers=user_a)
    assert res_a.status_code == 200

    res_b = await client.get("/api/financial/profile", headers=user_b)
    assert res_b.status_code == 404  # B has no profile — A's is invisible to B


async def test_cross_user_loan_isolation(client, user_a, user_b):
    create = await client.post("/api/financial/loans", json={
        "name": "A's Loan", "emi_amount": 5000,
    }, headers=user_a)
    loan_id = create.json()["id"]

    # B cannot deactivate A's loan
    res = await client.patch(f"/api/financial/loans/{loan_id}/deactivate", headers=user_b)
    assert res.status_code == 404

    # B's own loan list doesn't include A's loan
    res_b = await client.get("/api/financial/loans", headers=user_b)
    assert all(l["id"] != loan_id for l in res_b.json())


async def test_cross_user_credit_scenario_isolation(client, user_a, user_b):
    await client.put("/api/financial/profile", json={
        "monthly_income": 60000, "liquid_savings": 30000, "emergency_fund_target_months": 3,
    }, headers=user_a)
    create = await client.post("/api/credit-scenarios", json={
        "label": "A's Scenario", "proposed_amount": 500000,
        "annual_interest_rate": 9.5, "tenure_months": 60,
    }, headers=user_a)
    scenario_id = create.json()["id"]

    # B cannot include A's scenario in a compare call
    res = await client.post("/api/credit-scenarios/compare", json={
        "scenario_ids": [scenario_id, scenario_id],
    }, headers=user_b)
    assert res.status_code in (404, 422)

    res_b = await client.get("/api/credit-scenarios", headers=user_b)
    assert all(s["id"] != scenario_id for s in res_b.json()["items"])


async def test_cross_user_fraud_scan_isolation(client, user_a, user_b):
    await client.post("/api/fraud/analyse-text", json={
        "input_type": "sms", "text": "Share the OTP now.",
    }, headers=user_a)

    res_b = await client.get("/api/fraud/scans", headers=user_b)
    assert res_b.json()["total"] == 0


async def test_cross_user_copilot_conversation_isolation(client, user_a, user_b):
    res = await client.post("/api/copilot/chat", json={"message": "Hello"}, headers=user_a)
    conversation_id = res.json()["conversation_id"]

    # B cannot continue A's conversation
    res_b = await client.post("/api/copilot/chat", json={
        "message": "What did I just say?", "conversation_id": conversation_id,
    }, headers=user_b)
    assert res_b.status_code == 404


async def test_revoked_consent_blocks_access(client, user_a):
    res = await client.get("/api/consents", headers=user_a)
    financial_consent = next(c for c in res.json() if c["purpose"] == "financial_analysis")

    res = await client.get("/api/financial/health", headers=user_a)
    assert res.status_code in (200, 400)  # allowed (may lack profile data, but not blocked)

    await client.patch(f"/api/consents/{financial_consent['id']}/revoke", headers=user_a)

    res = await client.get("/api/financial/health", headers=user_a)
    assert res.status_code == 403


async def test_invalid_csv_upload_rejected(client, user_a):
    files = {"file": ("test.txt", b"not a csv", "text/plain")}
    res = await client.post("/api/transactions/upload", files=files, headers=user_a)
    assert res.status_code == 400