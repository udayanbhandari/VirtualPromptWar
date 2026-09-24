"""
Phase 3 Test Suite: Document Comparison & Structured Diff Feature
Tests /api/compare/ and DocumentComparator using the two freelance contract fixtures:
- freelance_contract_v1_favorable.txt (favorable terms)
- freelance_contract_v2_worse.txt (adverse / worse terms)
Confirms that the diff correctly pairs clauses, detects missing clauses, identifies risk deltas,
and determines that Version 1 is more favorable (or Version 2 increases risk / benefits user less).
"""

import sys
from pathlib import Path

# Add backend root to sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import FavorsParty

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_compare_freelance_contracts():
    v1_path = FIXTURES_DIR / "freelance_contract_v1_favorable.txt"
    v2_path = FIXTURES_DIR / "freelance_contract_v2_worse.txt"
    assert v1_path.exists(), f"Missing fixture: {v1_path}"
    assert v2_path.exists(), f"Missing fixture: {v2_path}"

    # 1. Ingest Favorable Contract (Doc A)
    with open(v1_path, "rb") as f:
        resp_a = client.post(
            "/api/ingest/",
            files={"file": ("freelance_contract_v1_favorable.txt", f, "text/plain")},
        )
    assert resp_a.status_code == 200, resp_a.text
    doc_id_a = resp_a.json()["docId"]

    # Extract clauses for Doc A
    resp_clauses_a = client.post(f"/api/clauses/{doc_id_a}")
    assert resp_clauses_a.status_code == 200, resp_clauses_a.text
    clauses_a = resp_clauses_a.json()["clauses"]
    assert len(clauses_a) >= 5, f"Expected >= 5 clauses for doc A, got {len(clauses_a)}"

    # 2. Ingest Worse Contract (Doc B)
    with open(v2_path, "rb") as f:
        resp_b = client.post(
            "/api/ingest/",
            files={"file": ("freelance_contract_v2_worse.txt", f, "text/plain")},
        )
    assert resp_b.status_code == 200, resp_b.text
    doc_id_b = resp_b.json()["docId"]

    # Extract clauses for Doc B
    resp_clauses_b = client.post(f"/api/clauses/{doc_id_b}")
    assert resp_clauses_b.status_code == 200, resp_clauses_b.text
    clauses_b = resp_clauses_b.json()["clauses"]
    assert len(clauses_b) >= 5, f"Expected >= 5 clauses for doc B, got {len(clauses_b)}"

    # 3. Call Compare Endpoint: POST /api/compare/
    compare_resp = client.post(
        "/api/compare/",
        json={"docIdA": doc_id_a, "docIdB": doc_id_b},
    )
    assert compare_resp.status_code == 200, compare_resp.text
    data = compare_resp.json()

    assert "comparison" in data, "Missing 'comparison' in compare response"
    comparison = data["comparison"]
    assert comparison["docIdA"] == doc_id_a
    assert comparison["docIdB"] == doc_id_b

    pairs = comparison["pairs"]
    assert len(pairs) >= 4, f"Expected at least 4 paired clauses, got {len(pairs)}"

    # Check each pair structure: topic, docA_text, docB_text, difference_summary, favors, riskDelta
    for pair in pairs:
        assert pair["topic"], "Missing topic"
        assert pair["docA_text"], "Missing docA_text"
        assert pair["docB_text"], "Missing docB_text"
        assert pair["difference_summary"], "Missing difference_summary"
        assert pair["favors"] in ["docA", "docB", "neutral"], f"Invalid favors: {pair['favors']}"
        assert pair["riskDelta"], "Missing riskDelta"

    # Verify overall assessment and favorability
    print(f"\n[OVERALL FAVORS]: {comparison['overallFavors']}")
    print(f"[OVERALL ASSESSMENT]: {comparison['overallAssessment']}")

    # Version 1 is favorable, Version 2 is adverse/worse.
    # Therefore, comparison should indicate docA favors the user or docB increases risk.
    assert comparison["overallFavors"] == FavorsParty.DOC_A.value, (
        f"Expected comparison to favor Doc A (favorable contract), got {comparison['overallFavors']}"
    )
    assert "Document A is significantly more favorable" in comparison["overallAssessment"] or "favorable" in comparison["overallAssessment"].lower()

    # Verify specific risk deltas across key clauses (Payment, Liability, Termination)
    topics = [p["topic"].lower() for p in pairs]
    print(f"[PAIRED TOPICS]: {topics}")

    doc_a_favored_count = sum(1 for p in pairs if p["favors"] == "docA")
    assert doc_a_favored_count >= 3, f"Expected >= 3 clauses favoring docA, got {doc_a_favored_count}"
    print(f"[PASS] Successfully verified {doc_a_favored_count} clauses favor Doc A over Doc B.")


def test_compare_missing_clauses():
    """Test comparison when one document has clauses that the other document does not have."""
    from app.services.document_store import document_store
    from app.models.schemas import Clause, ClauseCategory, DocumentSummary

    # Create synthetic doc with an extra arbitration clause and confidentiality clause
    doc_a_id = "test-doc-missing-a"
    doc_b_id = "test-doc-missing-b"

    clauses_a = [
        Clause(
            id="c1",
            text="Payment shall be Net 15 days.",
            category=ClauseCategory.PAYMENT,
            plain_language="Pay within 15 days.",
        ),
        Clause(
            id="c2",
            text="Disputes resolved by arbitration in Bengaluru.",
            category=ClauseCategory.ARBITRATION,
            plain_language="Arbitrate locally.",
        ),
    ]

    clauses_b = [
        Clause(
            id="c3",
            text="Payment shall be Net 60 days.",
            category=ClauseCategory.PAYMENT,
            plain_language="Pay within 60 days.",
        ),
        Clause(
            id="c4",
            text="All proprietary information shall be kept secret.",
            category=ClauseCategory.CONFIDENTIALITY,
            plain_language="Keep information confidential.",
        ),
    ]

    from app.services.document_store import DocumentRecord
    document_store.save(
        DocumentRecord(docId=doc_a_id, fileName="doc_a.txt", rawText="Payment shall be Net 15 days. Disputes resolved by arbitration in Bengaluru.", clauses=clauses_a)
    )
    document_store.save(
        DocumentRecord(docId=doc_b_id, fileName="doc_b.txt", rawText="Payment shall be Net 60 days. All proprietary information shall be kept secret.", clauses=clauses_b)
    )

    compare_resp = client.post(
        "/api/compare/",
        json={"docIdA": doc_a_id, "docIdB": doc_b_id},
    )
    assert compare_resp.status_code == 200, compare_resp.text
    data = compare_resp.json()["comparison"]

    missing = data["missingClauses"]
    assert len(missing) == 2, f"Expected 2 missing clause items, got {len(missing)}"

    # One present in docA missing in docB (Arbitration)
    missing_in_b = next((m for m in missing if m["presentIn"] == "docA" and m["missingFrom"] == "docB"), None)
    assert missing_in_b is not None
    assert "Arbitration" in missing_in_b["topic"]

    # One present in docB missing in docA (Confidentiality)
    missing_in_a = next((m for m in missing if m["presentIn"] == "docB" and m["missingFrom"] == "docA"), None)
    assert missing_in_a is not None
    assert "Confidentiality" in missing_in_a["topic"]
    print("\n[PASS] Successfully detected missing clauses between docA and docB.")
