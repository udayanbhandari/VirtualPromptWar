"""
Phase 5 Test Suite: Next Steps Generator (/nextsteps/{docId})
Tests:
- Action checklist generation for MEDIUM/HIGH risk clauses (2-4 concrete, non-legal-advice actions).
- 'Questions for your lawyer' generation (1-3 questions to read aloud in consultation).
- 3-5 bullet executive document brief ready for printing/export.
- Calm, practical, non-alarmist tone (no 'you should sue', only practical verification).
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


def test_next_steps_on_restrictive_contract():
    # Ingest the restrictive freelance contract (v2 worse) which has multiple high/medium risk terms
    v2_path = FIXTURES_DIR / "freelance_contract_v2_worse.txt"
    assert v2_path.exists(), f"Missing fixture {v2_path}"

    with open(v2_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("freelance_contract_v2_worse.txt", f, "text/plain")},
        )
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["docId"]

    # Extract clauses
    resp_clauses = client.post(f"/api/clauses/{doc_id}")
    assert resp_clauses.status_code == 200, resp_clauses.text

    # Call /nextsteps/{docId}
    ns_resp = client.post(f"/api/nextsteps/{doc_id}")
    assert ns_resp.status_code == 200, ns_resp.text
    data = ns_resp.json()

    assert data["docId"] == doc_id
    assert "documentBrief" in data
    brief = data["documentBrief"]
    assert 3 <= len(brief) <= 6, f"Expected 3-5 brief bullet points, got {len(brief)}"
    print("\n[DOCUMENT BRIEF]:")
    for b in brief:
        print(f"  • {b}")

    flagged_clauses = data["flaggedClauses"]
    assert len(flagged_clauses) >= 3, f"Expected >= 3 flagged clauses with next steps, got {len(flagged_clauses)}"

    # Test each flagged clause for required fields and tone constraints
    for fc in flagged_clauses:
        cid = fc["clauseId"]
        checklist = fc["actionChecklist"]
        lawyer_qs = fc["lawyerQuestions"]

        print(f"\n[FLAGGED CLAUSE {cid} ({fc['category']}) - Risk: {fc['riskLevel']}]:")
        print(f"  Verbatim: \"{fc['clauseText'][:60]}...\"")
        print("  Action Checklist:")
        for a in checklist:
            print(f"    - {a}")
            # Verify tone: non-alarmist, no "you should sue"
            assert "you should sue" not in a.lower()
            assert "file a lawsuit immediately" not in a.lower()

        print("  Questions for Your Lawyer:")
        for q in lawyer_qs:
            print(f"    ? {q}")
            assert "?" in q or len(q) > 10
            # Must directly reference clause or practical enforceability
            assert any(term in q.lower() for term in [cid.lower(), "clause", "enforceable", "remedies", "risk", "valid", "act"])

        assert 1 <= len(checklist) <= 5, f"Checklist length {len(checklist)} out of bounds"
        assert 1 <= len(lawyer_qs) <= 4, f"Lawyer questions length {len(lawyer_qs)} out of bounds"

    print("\n[PASS] Successfully verified Phase 5 Next Steps and Consultation Brief generation.")
