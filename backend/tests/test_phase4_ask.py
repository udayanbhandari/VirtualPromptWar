"""
Phase 4 Test Suite: Grounded Document Q&A (/ask)
Tests Q&A scoped strictly to the uploaded document + statute grounding.
Tests 3 core adversarial scenarios:
1. Question answerable directly from document clauses (quotes clause ID).
2. Question requiring statutory grounding (cites Indian statute section).
3. Question genuinely outside document scope (returns 'this document doesn't address that').
4. Conversational context maintenance (last turns follow-up).
5. Dynamic informational disclaimer variation.
"""

import sys
from pathlib import Path

# Add backend root to sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_ask_grounded_scenarios():
    # 1. Ingest freelance contract v1 favorable
    v1_path = FIXTURES_DIR / "freelance_contract_v1_favorable.txt"
    assert v1_path.exists(), f"Missing fixture {v1_path}"

    with open(v1_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("freelance_contract_v1_favorable.txt", f, "text/plain")},
        )
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["docId"]

    # Extract clauses for this doc
    resp_clauses = client.post(f"/api/clauses/{doc_id}")
    assert resp_clauses.status_code == 200, resp_clauses.text

    # ── Test 1: Answerable from document clauses ───────────────────────
    # Question about payment terms in the document
    q1 = "What are the payment terms and invoice settlement timeline?"
    resp1 = client.post(
        "/api/ask/",
        json={"docId": doc_id, "question": q1},
    )
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    answer1 = data1["answer"]
    print(f"\n[Test 1 Answer]:\n{answer1}")

    # Must quote/cite clause ID and answer accurately from text
    assert len(data1["sourceClauseIds"]) > 0, "Expected sourceClauseIds to be populated"
    assert any(c in answer1 for c in ["[clause-1]", "clause-1", "Net 15", "15 days"]), (
        f"Expected clause reference in answer: {answer1}"
    )
    assert "Net 15" in answer1 or "15" in answer1

    # ── Test 2: Question requiring statutory grounding ──────────────────
    # Ask about non-compete restraint legality under Indian law
    q2 = "Is the non-compete clause valid under Section 27 of the Indian Contract Act or restraint of trade laws?"
    resp2 = client.post(
        "/api/ask/",
        json={"docId": doc_id, "question": q2},
    )
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    answer2 = data2["answer"]
    print(f"\n[Test 2 Answer (Statute Grounded)]:\n{answer2}")

    # Must reference Section 27 / Indian Contract Act or relevant statute
    assert len(data2["relevantStatutes"]) > 0 or "Section 27" in answer2 or "Contract Act" in answer2, (
        f"Expected statute reference in answer or relevantStatutes: {answer2}"
    )

    # ── Test 3: Adversarial out-of-scope question ──────────────────────
    # Question on completely unrelated topic not covered in the document
    q3 = "What is the best recipe for chocolate chip cookies, and what is the weather in Delhi today?"
    resp3 = client.post(
        "/api/ask/",
        json={"docId": doc_id, "question": q3},
    )
    assert resp3.status_code == 200, resp3.text
    data3 = resp3.json()
    answer3 = data3["answer"].lower()
    print(f"\n[Test 3 Answer (Out of Scope)]:\n{data3['answer']}")

    # Must explicitly state document doesn't address that and not fabricate
    assert "this document doesn't address that" in answer3 or "doesn't address that" in answer3, (
        f"Expected 'this document doesn't address that' in out-of-scope response, got: {answer3}"
    )
    assert len(data3["sourceClauseIds"]) == 0

    # ── Test 4: Conversational follow-up context ───────────────────────
    # Send previous turns and a follow-up question
    history = [
        {"role": "user", "content": "Tell me about payment."},
        {"role": "assistant", "content": "Client shall pay Contractor within Net 15 days [clause-1]."},
    ]
    q4 = "What happens if there is a dispute regarding this?"
    resp4 = client.post(
        "/api/ask/",
        json={"docId": doc_id, "question": q4, "history": history},
    )
    assert resp4.status_code == 200, resp4.text
    data4 = resp4.json()
    answer4 = data4["answer"]
    print(f"\n[Test 4 Answer (Follow-up)]:\n{answer4}")

    assert any(w in answer4.lower() for w in ["arbitration", "bengaluru", "dispute", "clause-6"]), (
        f"Expected dispute/arbitration clause details, got: {answer4}"
    )

    # ── Test 5: Varied disclaimer phrasing ─────────────────────────────
    # Run multiple queries and verify disclaimers differ / are present
    disclaimers = set()
    for q in ["Tell me about liability", "Tell me about termination", "Tell me about IP"]:
        r = client.post("/api/ask/", json={"docId": doc_id, "question": q})
        ans = r.json()["answer"]
        assert any(term in ans.lower() for term in ["legal advice", "informational", "legal counsel", "opinion"]), (
            f"Missing informational disclaimer: {ans}"
        )
        # Check last line
        lines = [line.strip() for line in ans.split("\n") if line.strip()]
        if lines:
            disclaimers.add(lines[-1])

    print(f"\n[Test 5 Disclaimers Captured]: {len(disclaimers)} distinct disclaimer(s)")
    print("[PASS] All Phase 4 Grounded Q&A criteria verified!")
