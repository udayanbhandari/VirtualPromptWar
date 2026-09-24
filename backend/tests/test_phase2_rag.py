"""
Phase 2 Test Suite: Statute Grounding & RAG Retrieval
Tests ChromaDB indexing, retrieve_relevant_law, and statute grounding in riskReason.
"""

import asyncio
import sys
from pathlib import Path

# Add backend root to sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from app.services.vector_store import vector_store, retrieve_relevant_law
from app.services.gemini_client import gemini_client
from app.models.schemas import Clause, ClauseCategory, RiskLevel


async def test_statute_indexing():
    print("\n--- Testing ChromaDB Statute Indexing ---")
    count = vector_store.collection.count()
    print(f"Total statutory sections indexed in ChromaDB: {count}")
    assert count >= 20, f"Expected at least 20 statutory chunks, got {count}"
    print("[PASS] Indian statutes properly indexed in ChromaDB collection 'indian_statutes'.")


async def test_retrieval_accuracy():
    print("\n--- Testing Statute Retrieval Relevance ---")

    # Test 1: Badly-written termination with penalty & forfeiture
    q1 = "Tenant may terminate upon 5 days notice but forfeits entire deposit and pays 6 months liquidated penalty"
    r1 = await retrieve_relevant_law(q1, top_k=3)
    print(f"\nQuery 1 (Termination & Penalty): '{q1[:60]}...'")
    for i, m in enumerate(r1):
        print(f"  {i+1}. {m['citation']} - {m['title']} (sim: {m['similarity']})")

    top1 = r1[0]["citation"]
    assert any(s in top1 for s in ["Section 74", "Section 2(46)", "Section 39"]), (
        f"Expected Section 74, 2(46), or 39, got {top1}"
    )
    print("  [PASS] Relevant Contract Act / Consumer Protection Act section surfaced!")

    # Test 2: Restraint of trade / non-compete
    q2 = "Employee is restrained from practicing their profession or engaging in competing business for 5 years"
    r2 = await retrieve_relevant_law(q2, top_k=3)
    print(f"\nQuery 2 (Restraint of Trade): '{q2[:60]}...'")
    for i, m in enumerate(r2):
        print(f"  {i+1}. {m['citation']} - {m['title']} (sim: {m['similarity']})")

    assert "Section 27" in r2[0]["citation"], f"Expected Section 27, got {r2[0]['citation']}"
    print("  [PASS] Section 27 (Agreement in restraint of trade void) correctly surfaced!")

    # Test 3: Unilateral indemnity without fault
    q3 = "Contractor agrees to indemnify Client against all claims and damages regardless of whether Client was negligent"
    r3 = await retrieve_relevant_law(q3, top_k=3)
    print(f"\nQuery 3 (Indemnity): '{q3[:60]}...'")
    for i, m in enumerate(r3):
        print(f"  {i+1}. {m['citation']} - {m['title']} (sim: {m['similarity']})")

    assert any(s in r3[0]["citation"] for s in ["Section 124", "Section 125"]), (
        f"Expected Section 124/125, got {r3[0]['citation']}"
    )
    print("  [PASS] Section 124/125 (Contract of indemnity) correctly surfaced!")

    # Test 4: Sensitive personal data & cybersecurity
    q4 = "Company shall not be required to maintain reasonable security practices for sensitive personal customer data"
    r4 = await retrieve_relevant_law(q4, top_k=3)
    print(f"\nQuery 4 (Data Protection): '{q4[:60]}...'")
    for i, m in enumerate(r4):
        print(f"  {i+1}. {m['citation']} - {m['title']} (sim: {m['similarity']})")

    assert any(s in r4[0]["citation"] for s in ["Section 43A", "Section 6", "Section 8", "DPDP"]), (
        f"Expected IT Act Sec 43A or DPDP Act, got {r4[0]['citation']}"
    )
    print("  [PASS] Information Technology Act / DPDP Act correctly surfaced!")


async def test_clause_statute_grounding():
    print("\n--- Testing Clause Statute Grounding in Risk Reasoning ---")

    # High-risk clause with penalty & forfeiture
    clause_penalty = Clause(
        id="test-clause-pen",
        text="Any attempt to vacate early forfeits the entire security deposit and accelerates all remaining 10 months rent as a liquidated penalty.",
        category=ClauseCategory.TERMINATION,
        plainLanguage="Vacating early forfeits all deposit and demands immediate payment of 10 months rent.",
        riskLevel=RiskLevel.HIGH,
        riskReason="may warrant review because it accelerates rent upon vacancy.",
        conflictsWith=[],
    )

    grounded = await gemini_client._ground_clauses_with_statutes([clause_penalty])
    reason = grounded[0].risk_reason
    print(f"Grounded riskReason: {reason}")
    assert "Section 74" in reason or "Section 2(46)" in reason, (
        f"Expected Section 74 or 2(46) citation in riskReason, got: {reason}"
    )
    print("  [PASS] High-risk penalty clause grounded with Section 74 / Section 2(46) citation!")

    # Low-risk standard clause should NOT have forced citation
    clause_low = Clause(
        id="test-clause-low",
        text="Monthly rent of $2,000 shall be paid by bank transfer on the 1st of each calendar month.",
        category=ClauseCategory.PAYMENT,
        plainLanguage="Rent is $2,000 due on the first of each month.",
        riskLevel=RiskLevel.LOW,
        riskReason="Standard payment term.",
        conflictsWith=[],
    )
    grounded_low = await gemini_client._ground_clauses_with_statutes([clause_low])
    assert "Section" not in grounded_low[0].risk_reason, "Low-risk clause should not force statutory citations!"
    print("  [PASS] Low-risk clause did not receive forced statutory citations!")


def main():
    asyncio.run(test_statute_indexing())
    asyncio.run(test_retrieval_accuracy())
    asyncio.run(test_clause_statute_grounding())
    print("\n=======================================================")
    print("ALL PHASE 2 STATUTE GROUNDING TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")


if __name__ == "__main__":
    main()
