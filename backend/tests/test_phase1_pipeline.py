"""
Phase 1 Test Suite: Document Ingestion + Clause Extraction Pipeline
Tests /api/ingest/ and /api/clauses/{doc_id} using real sample fixtures.
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


def test_ingest_and_extract_rental_agreement():
    pdf_path = FIXTURES_DIR / "rental_agreement.pdf"
    assert pdf_path.exists(), f"Missing fixture: {pdf_path}"

    # 1. Ingest PDF
    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("rental_agreement.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    doc_id = data["docId"]
    assert doc_id.startswith("doc-")
    assert len(data["rawText"]) > 0
    print(f"\n[PASS] Ingested rental_agreement.pdf -> docId: {doc_id} ({len(data['rawText'])} chars text)")

    # 2. Extract clauses via POST /api/clauses/{docId}
    c_resp = client.post(f"/api/clauses/{doc_id}")
    assert c_resp.status_code == 200, c_resp.text
    c_data = c_resp.json()
    clauses = c_data["clauses"]
    assert len(clauses) >= 4, f"Expected at least 4 clauses, got {len(clauses)}"

    # Check clause fields & intra-document conflict detection
    has_conflict = False
    for c in clauses:
        assert c["id"], "Missing clause id"
        assert c["text"], "Missing clause text"
        assert c["category"] in [
            "payment", "termination", "liability", "indemnity",
            "auto_renewal", "arbitration", "confidentiality", "other"
        ], f"Invalid category {c['category']}"
        assert c["plainLanguage"], "Missing plainLanguage"
        assert c["riskLevel"] in ["low", "medium", "high", "critical"], f"Invalid riskLevel {c['riskLevel']}"
        assert "may warrant review because" in c["riskReason"].lower() or len(c["riskReason"]) > 10

        if len(c["conflictsWith"]) > 0:
            has_conflict = True
            print(f"  [CONFLICT] Detected Conflict: {c['id']} ({c['category']}) conflicts with {c['conflictsWith']}")

    assert has_conflict, "Expected intra-document conflict to be detected in rental agreement (early termination vs absolute term/forfeiture)"
    print(f"[PASS] Extracted {len(clauses)} clauses with intra-document conflict detection.")


def test_ingest_and_extract_freelance_nda():
    pdf_path = FIXTURES_DIR / "freelance_nda.pdf"
    assert pdf_path.exists(), f"Missing fixture: {pdf_path}"

    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("freelance_nda.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["docId"]

    c_resp = client.post(f"/api/clauses/{doc_id}")
    assert c_resp.status_code == 200, c_resp.text
    clauses = c_resp.json()["clauses"]

    # Verify conflict between 2-year expiration and perpetual survival
    conflicted = [c for c in clauses if len(c["conflictsWith"]) > 0]
    assert len(conflicted) >= 2, "Expected 2-year confidentiality vs perpetual survival conflict"
    print(f"\n[PASS] Freelance NDA -> conflict detected between: {[c['id'] for c in conflicted]}")


def test_ingest_and_extract_loan_agreement():
    pdf_path = FIXTURES_DIR / "loan_agreement.pdf"
    assert pdf_path.exists(), f"Missing fixture: {pdf_path}"

    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("loan_agreement.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["docId"]

    c_resp = client.post(f"/api/clauses/{doc_id}")
    assert c_resp.status_code == 200, c_resp.text
    clauses = c_resp.json()["clauses"]

    # Verify conflict between prepayment privilege and mandatory penalty
    conflicted = [c for c in clauses if len(c["conflictsWith"]) > 0]
    assert len(conflicted) >= 2, "Expected prepayment privilege vs penalty conflict"
    print(f"\n[PASS] Loan Agreement -> conflict detected between: {[c['id'] for c in conflicted]}")


def test_get_clauses_with_filtering():
    # Ingest rental agreement
    pdf_path = FIXTURES_DIR / "rental_agreement.pdf"
    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/ingest/",
            files={"file": ("rental_agreement.pdf", f, "application/pdf")},
        )
    doc_id = resp.json()["docId"]

    # Ensure extracted
    client.post(f"/api/clauses/{doc_id}")

    # Test GET with category filter
    resp = client.get(f"/api/clauses/{doc_id}?category=termination")
    assert resp.status_code == 200
    filtered = resp.json()["clauses"]
    assert all(c["category"] == "termination" for c in filtered)
    print(f"\n[PASS] GET filter by category=termination: returned {len(filtered)} clauses")

    # Test GET with riskLevel filter
    resp = client.get(f"/api/clauses/{doc_id}?riskLevel=high")
    assert resp.status_code == 200
    filtered_high = resp.json()["clauses"]
    assert all(c["riskLevel"] == "high" for c in filtered_high)
    print(f"[PASS] GET filter by riskLevel=high: returned {len(filtered_high)} clauses")


def test_ingest_image_format():
    # Test image upload
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    resp = client.post(
        "/api/ingest/",
        files={"file": ("contract_scan.png", dummy_png, "image/png")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mimeType"] == "image/png"
    print(f"\n[PASS] Ingest image/png accepted: docId {data['docId']}")


if __name__ == "__main__":
    test_ingest_and_extract_rental_agreement()
    test_ingest_and_extract_freelance_nda()
    test_ingest_and_extract_loan_agreement()
    test_get_clauses_with_filtering()
    test_ingest_image_format()
    print("\n=======================================================")
    print("ALL PHASE 1 TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")
