# ClauseWise — 2-to-3 Minute Live Demo Script

This script walks through every core feature of **ClauseWise** using the sample rental agreement and consulting fixtures. Follow the steps in order to demonstrate all official use cases in one smooth pass.

---

## Pre-Demo Checklist (30s before presentation)

- [ ] **Backend running:** `uvicorn app.main:app --reload --port 8000` (from `backend/`)
- [ ] **Frontend running:** `npm run dev` (from `frontend/` at `http://localhost:5173`)
- [ ] **Health check verified:** `http://localhost:8000/api/health` returns `{"status":"ok"}`
- [ ] **Fixtures ready:** `backend/fixtures/rental_agreement.pdf` and `backend/fixtures/rental_agreement_v2_favorable.pdf`

---

## Live Demo Flow (2–3 Minutes)

```
[Upload Rental Agreement] ──> [Risk & Inconsistency Dashboard] ──> [Compare with Version 2]
                                                                        │
[Export Consultation Brief] <── [Grounded Document Q&A (/ask)] <────────┘
```

---

### Step 1: Upload Rental Agreement & Inconsistency Detection (45s)

1. **Action:** On the **Upload** screen, drag and drop `backend/fixtures/rental_agreement.pdf` (or browse and select it).
2. **What Happens:** Multimodal extraction processes the document, parses individual contractual clauses, normalizes categories, and identifies risks.
3. **Talking Points & UI Highlights:**
   - **Visual Risk Badges:** Point out the color-coded hierarchy (`LOW` = slate green, `MEDIUM` = amber, `HIGH` = crimson).
   - **Plain Language Translation:** Point to Clause 3 (Access & Inspection) showing the plain-English translation: *"The landlord can enter the home whenever they want without giving any advance notice."*
   - **Intra-Document Inconsistency Flag:** Point out the prominent conflict link between **Clause 4** (Early Termination allowing 30 days notice) and **Clause 9** (Absolute 12-month commitment forfeiting deposit and accelerating rent).
   - **Statute Grounding:** Show that Clause 9 cites *Section 74 of the Indian Contract Act / Section 2(46) Consumer Protection Act* regarding unlawful liquidated penalties and unconscionable acceleration.

> **Speaker Note:** *"ClauseWise doesn't just read contracts; it catches hidden internal contradictions that standard legal scans miss. Here, Clause 4 promises early exit, but Clause 9 secretly penalizes it with complete deposit forfeiture."*

---

### Step 2: Compare Against Second Version (45s)

1. **Action:** Upload the second document `rental_agreement_v2_favorable.pdf` (or use the pre-filled Document B ID).
2. **Action:** Navigate to the **Compare** tab, select both document IDs, and click **Compare Documents**.
3. **What Happens:** Side-by-side clause alignment by topic and semantic similarity, with visual favor indicators.
4. **Talking Points & UI Highlights:**
   - **Executive Comparison Summary:** Point to the top banner: *"Document B is significantly more favorable to the tenant across key terms."*
   - **Side-by-Side Clause Pairs:** Show the **Termination** comparison: Version 1 imposes full term acceleration, while Version 2 provides 30-day notice with zero penalty.
   - **Risk Delta:** Highlight the risk reduction explanation (*"Decreases risk: removes liquidated penalty and restores notice period"*).
   - **Missing Clauses Section:** Point out clauses present only in Document A vs Document B.

> **Speaker Note:** *"When presented with a revised lease, ClauseWise instantly aligns matched clauses side-by-side so the user immediately knows whether a revision improved their protections or snuck in new liabilities."*

---

### Step 3: Grounded Document Q&A — Not a Chatbot (30s)

1. **Action:** Navigate to the **Ask** tab docked alongside the document clauses.
2. **Action:** Type: **"Can the landlord enter my apartment without notice?"**
3. **What Happens:** Instant grounded answer citing `[clause-3]` and quoting the specific lease language.
4. **Action (Adversarial test):** Type: **"What is the best recipe for chocolate cake?"**
5. **What Happens:** ClauseWise cleanly replies: *"This document doesn't address that. The provided contract does not contain any provisions relating to your query."*
6. **Talking Points & UI Highlights:**
   - **Strict Grounding:** Answers cite exact clause IDs (`[clause-3]`) which are clickable to jump to the clause.
   - **Statutory Context:** When relevant, Indian legal statutes are referenced to explain legal boundaries.
   - **Dynamic Disclaimers:** Notice the varied, non-repetitive informational disclaimer ending each answer.
   - **Anti-Hallucination:** Strictly refuses to answer off-topic queries.

> **Speaker Note:** *"This is not a general-purpose chatbot that hallucinates legal advice. It is strictly scoped to the four corners of this uploaded contract and applicable statutory provisions."*

---

### Step 4: Next Steps & Consultation Brief Export (30s)

1. **Action:** Navigate to the **Next Steps** tab and click **Generate Consultation Brief**.
2. **What Happens:** Gemini synthesizes flagged risks into an actionable checklist, lawyer consultation questions, and an executive brief.
3. **Talking Points & UI Highlights:**
   - **Action Checklist:** Practical, non-legal actions (e.g. *"Request landlord to add 24-hour advance written notice requirement"*).
   - **Questions for Your Lawyer:** Specific questions the tenant can read aloud (e.g. *"Under Section 74, is the automatic deposit forfeiture in clause 9 legally enforceable?"*).
   - **Export Brief:** Click **Export Brief** to open the clean, printable consultation one-pager.

> **Speaker Note:** *"Instead of vague warnings, ClauseWise prepares users for an efficient, cost-effective lawyer consultation with exact questions and a print-ready briefing document."*

---

## Quick Reference: Sample Contracts & Fixtures

| Document | Primary Use Case | Key Contractual Signals |
|---|---|---|
| `rental_agreement.pdf` | Inconsistency & High Risk | 30-day exit vs absolute forfeiture conflict; unannounced entry |
| `rental_agreement_v2_favorable.pdf` | Comparison Baseline | 24-hr entry notice, refundable deposit, zero-penalty exit |
| `freelance_contract_v1_favorable.pdf` | Favorable Benchmark | Net 15, fee-capped liability, bilateral 30-day notice |
| `freelance_contract_v2_worse.pdf` | Restrictive Benchmark | Net 60, uncapped liability, 24-month worldwide non-compete |
| `freelance_nda.pdf` | Conflict Detection | 2-year confidentiality vs perpetual survival conflict |
| `loan_agreement.pdf` | Statutory Grounding | 8% liquidated penalty vs Section 74 Indian Contract Act |

---

## Key Differentiators to Emphasize

1. **Intra-Document Conflict Detection:** Automatically detects conflicting terms within the same contract.
2. **Statutory Grounding (RAG):** Evaluates clause risks against indexed Indian statutes (Contract Act, Consumer Protection Act, DPDP Act) without forced citations.
3. **Grounded Bounded Q&A:** Scoped only to document clauses; explicitly declines off-topic questions.
4. **Actionable Consultation Prep:** Generates concrete questions for users to read directly to counsel.
