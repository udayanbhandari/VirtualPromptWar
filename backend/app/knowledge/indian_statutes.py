"""
Curated plain-text statutory excerpts from Indian Law relevant to contract analysis:
1. Indian Contract Act, 1872 (ICA)
2. Consumer Protection Act, 2019 (CPA)
3. Information Technology Act, 2000 (IT Act)
4. Digital Personal Data Protection Act, 2023 (DPDP Act)

Each chunk is focused on contractual terms: formation, breach, damages, penalty stipulations,
unfair terms, indemnity, restraint of trade/dispute, and digital data handling.
"""

from typing import TypedDict


class StatuteChunk(TypedDict):
    id: str
    act: str
    section: str
    citation: str
    title: str
    category: str
    text: str


STATUTE_CHUNKS: list[StatuteChunk] = [
    # ── INDIAN CONTRACT ACT, 1872 ─────────────────────────────────────
    {
        "id": "ica-sec10",
        "act": "Indian Contract Act, 1872",
        "section": "Section 10",
        "citation": "Section 10, Indian Contract Act, 1872",
        "title": "What agreements are contracts",
        "category": "formation",
        "text": (
            "Section 10 states that all agreements are contracts if they are made by the free consent "
            "of parties competent to contract, for a lawful consideration and with a lawful object, and "
            "are not hereby expressly declared to be void. Any contract lacking free consent or lawful "
            "consideration is vulnerable to challenge."
        ),
    },
    {
        "id": "ica-sec14",
        "act": "Indian Contract Act, 1872",
        "section": "Section 14",
        "citation": "Section 14, Indian Contract Act, 1872",
        "title": "Free consent defined",
        "category": "formation",
        "text": (
            "Section 14 defines consent as free when it is not caused by coercion (Section 15), "
            "undue influence (Section 16), fraud (Section 17), misrepresentation (Section 18), "
            "or mistake (Sections 20, 21, and 22). When consent to an agreement is caused by undue "
            "influence or coercion, the agreement is a contract voidable at the option of the party whose "
            "consent was so caused."
        ),
    },
    {
        "id": "ica-sec16",
        "act": "Indian Contract Act, 1872",
        "section": "Section 16",
        "citation": "Section 16, Indian Contract Act, 1872",
        "title": "Undue influence and unconscionable bargains",
        "category": "unfair_terms",
        "text": (
            "Section 16 provides that a contract is induced by undue influence where one of the parties "
            "is in a position to dominate the will of the other and uses that position to obtain an unfair "
            "advantage. Where a party in a dominant bargaining position enters into a transaction that "
            "appears on the face of it or on evidence to be unconscionable, the burden of proving that the "
            "contract was not induced by undue influence lies upon the dominating party."
        ),
    },
    {
        "id": "ica-sec23",
        "act": "Indian Contract Act, 1872",
        "section": "Section 23",
        "citation": "Section 23, Indian Contract Act, 1872",
        "title": "What considerations and objects are lawful, and what not",
        "category": "formation",
        "text": (
            "Section 23 provides that the consideration or object of an agreement is lawful unless it is "
            "forbidden by law, or is of such a nature that if permitted it would defeat the provisions of "
            "any law, or is fraudulent, or involves injury to the person or property of another, or the "
            "Court regards it as immoral or opposed to public policy. Every agreement of which the object "
            "or consideration is unlawful is void."
        ),
    },
    {
        "id": "ica-sec27",
        "act": "Indian Contract Act, 1872",
        "section": "Section 27",
        "citation": "Section 27, Indian Contract Act, 1872",
        "title": "Agreement in restraint of trade void",
        "category": "restraint_of_trade",
        "text": (
            "Section 27 mandates that every agreement by which anyone is restrained from exercising a lawful "
            "profession, trade, or business of any kind is to that extent void. Indian courts strictly construe "
            "post-termination non-compete clauses against employers and contracting parties, treating post-contractual "
            "restrictions on an individual's right to work as void under this section, saving only the sale of goodwill."
        ),
    },
    {
        "id": "ica-sec28",
        "act": "Indian Contract Act, 1872",
        "section": "Section 28",
        "citation": "Section 28, Indian Contract Act, 1872",
        "title": "Agreements in restraint of legal proceedings void",
        "category": "arbitration_jurisdiction",
        "text": (
            "Section 28 provides that every agreement by which any party is restricted absolutely from enforcing "
            "their contractual rights in ordinary tribunals, or which limits the time within which they may enforce "
            "their rights, or which extinguishes the rights of any party upon the expiry of a specified period, is void "
            "to that extent. Clauses completely barring access to courts or imposing unreasonably truncated limitation "
            "periods violate this provision, though valid arbitration agreements are protected under Exception 1."
        ),
    },
    {
        "id": "ica-sec39",
        "act": "Indian Contract Act, 1872",
        "section": "Section 39",
        "citation": "Section 39, Indian Contract Act, 1872",
        "title": "Effect of refusal of party to perform promise wholly",
        "category": "termination",
        "text": (
            "Section 39 states that when a party to a contract has refused to perform, or disabled themselves from "
            "performing, their promise in its entirety, the promisee may put an end to the contract unless the promisee "
            "has signified by words or conduct their acquiescence in its continuance. Unilateral termination without cause "
            "or without reasonable cure notice may trigger wrongful repudiation under this section if the counterparty has "
            "not refused performance."
        ),
    },
    {
        "id": "ica-sec55",
        "act": "Indian Contract Act, 1872",
        "section": "Section 55",
        "citation": "Section 55, Indian Contract Act, 1872",
        "title": "Effect of failure to perform at fixed time when time is essential",
        "category": "performance",
        "text": (
            "Section 55 provides that when a party fails to do a certain thing at or before a specified time in a contract "
            "where time is of the essence, the contract or so much of it as has not been performed becomes voidable at the "
            "option of the promisee. If time is not essential, the promisee is entitled to compensation for any loss occasioned "
            "by the delay, but cannot terminate immediately without giving reasonable notice making time essential."
        ),
    },
    {
        "id": "ica-sec56",
        "act": "Indian Contract Act, 1872",
        "section": "Section 56",
        "citation": "Section 56, Indian Contract Act, 1872",
        "title": "Agreement to do impossible act and doctrine of frustration",
        "category": "termination",
        "text": (
            "Section 56 codifies the doctrine of frustration: a contract to do an act which, after the contract is made, "
            "becomes impossible or by reason of some event which the promisor could not prevent becomes unlawful, becomes void "
            "when the act becomes impossible or unlawful. Parties cannot enforce performance or penalty damages when the underlying "
            "contract is discharged by supervening impossibility or force majeure."
        ),
    },
    {
        "id": "ica-sec73",
        "act": "Indian Contract Act, 1872",
        "section": "Section 73",
        "citation": "Section 73, Indian Contract Act, 1872",
        "title": "Compensation for loss or damage caused by breach of contract",
        "category": "breach",
        "text": (
            "Section 73 establishes the fundamental rule of unliquidated damages: when a contract is broken, the party who suffers "
            "from the breach is entitled to receive compensation for any loss or damage naturally arising in the usual course of things "
            "from such breach, or which the parties knew to be likely to result. Compensation is not given for any remote and indirect "
            "loss or damage. Total exclusions of liability or unreasonable liability caps must be balanced against actual proved damages."
        ),
    },
    {
        "id": "ica-sec74",
        "act": "Indian Contract Act, 1872",
        "section": "Section 74",
        "citation": "Section 74, Indian Contract Act, 1872",
        "title": "Compensation for breach of contract where penalty stipulated for",
        "category": "penalty",
        "text": (
            "Section 74 stipulates that when a contract contains a named amount or penalty stipulation for breach (such as liquidated "
            "damages, exorbitant interest acceleration, or forfeiture of security deposit/advance payments), the aggrieved party is entitled "
            "only to receive reasonable compensation not exceeding the penalty amount, whether or not actual damage is proved. Indian courts "
            "will not enforce in terrorem or punitive clauses that seek to penalize rather than genuinely pre-estimate reasonable loss."
        ),
    },
    {
        "id": "ica-sec124",
        "act": "Indian Contract Act, 1872",
        "section": "Section 124",
        "citation": "Section 124, Indian Contract Act, 1872",
        "title": "Contract of indemnity defined",
        "category": "indemnity",
        "text": (
            "Section 124 defines a contract of indemnity as an agreement whereby one party promises to save the other from loss caused "
            "to them by the conduct of the promisor themselves, or by the conduct of any other person. Broad clauses compelling one party "
            "to indemnify another for losses caused by the indemnified party's own negligence or fault fall outside standard statutory indemnity "
            "and are subjected to strict judicial scrutiny."
        ),
    },
    {
        "id": "ica-sec125",
        "act": "Indian Contract Act, 1872",
        "section": "Section 125",
        "citation": "Section 125, Indian Contract Act, 1872",
        "title": "Rights of indemnity-holder when sued",
        "category": "indemnity",
        "text": (
            "Section 125 grants the indemnity-holder the right to recover all damages, costs, and compromise sums incurred in defending "
            "claims covered by the indemnity, provided the indemnity-holder acted prudently and did not contravene the orders of the promisor. "
            "Unilateral indemnity provisions that exclude the indemnifying party from participating in or directing the defense may be challenged."
        ),
    },

    # ── CONSUMER PROTECTION ACT, 2019 ────────────────────────────────
    {
        "id": "cpa-sec2-46",
        "act": "Consumer Protection Act, 2019",
        "section": "Section 2(46)",
        "citation": "Section 2(46), Consumer Protection Act, 2019",
        "title": "Definition of unfair contract",
        "category": "unfair_terms",
        "text": (
            "Section 2(46) defines an 'unfair contract' between a manufacturer or trader or service provider and a consumer as having terms "
            "that cause significant change in consumer rights, including: (i) requiring excessive security deposits; (ii) imposing disproportionate "
            "penalty for breach; (iii) refusing early repayment of debts; (iv) entitling unilateral termination without reasonable cause; "
            "(v) permitting unilateral assignment to consumer's detriment; or (vi) imposing unreasonable charge, obligation, or condition. "
            "Consumer Commissions have express statutory power to declare such contract terms null and void."
        ),
    },
    {
        "id": "cpa-sec2-47",
        "act": "Consumer Protection Act, 2019",
        "section": "Section 2(47)",
        "citation": "Section 2(47), Consumer Protection Act, 2019",
        "title": "Unfair trade practice",
        "category": "unfair_terms",
        "text": (
            "Section 2(47) defines unfair trade practice as any deceptive trade practice adopting unfair methods for promoting sale or supply of "
            "goods or services, including misleading representations regarding standard, quality, performance characteristics, or warranty exclusions. "
            "Clauses that disclaim statutory warranties or deceptively disguise recurring auto-renewals without affirmative disclosure fall within "
            "prohibited unfair trade practices."
        ),
    },
    {
        "id": "cpa-sec84",
        "act": "Consumer Protection Act, 2019",
        "section": "Section 84",
        "citation": "Section 84, Consumer Protection Act, 2019",
        "title": "Liability of product service provider",
        "category": "liability",
        "text": (
            "Section 84 holds product service providers strictly liable for harm caused by deficiency in service, breach of express warranty, "
            "or failure to conform to standards. Standard contract clauses attempting to disclaim all liability for physical harm, property damage, "
            "or severe service deficiency to consumers cannot override this statutory product and service liability."
        ),
    },

    # ── INFORMATION TECHNOLOGY ACT, 2000 ─────────────────────────────
    {
        "id": "it-sec43a",
        "act": "Information Technology Act, 2000",
        "section": "Section 43A",
        "citation": "Section 43A, Information Technology Act, 2000",
        "title": "Compensation for failure to protect sensitive personal data",
        "category": "data_protection",
        "text": (
            "Section 43A mandates that where a body corporate possesses, deals, or handles any sensitive personal data or information in a "
            "computer resource that it owns, controls, or operates, and is negligent in implementing and maintaining reasonable security practices "
            "and procedures, causing wrongful loss or wrongful gain to any person, such body corporate shall be liable to pay damages by way "
            "of compensation to the person so affected. Contractual disclaimers of cybersecurity and data protection obligations are ineffective."
        ),
    },
    {
        "id": "it-sec72a",
        "act": "Information Technology Act, 2000",
        "section": "Section 72A",
        "citation": "Section 72A, Information Technology Act, 2000",
        "title": "Punishment for disclosure of information in breach of lawful contract",
        "category": "data_protection",
        "text": (
            "Section 72A prescribes criminal penalties (imprisonment up to three years, or fine up to five lakh rupees, or both) for any person "
            "who, having secured access to any material or personal information under the terms of a lawful contract, discloses such information "
            "without the consent of the person concerned, or in breach of a lawful contract, with intent to cause or knowing that it is likely to cause "
            "wrongful loss or wrongful gain."
        ),
    },

    # ── DIGITAL PERSONAL DATA PROTECTION ACT, 2023 ───────────────────
    {
        "id": "dpdp-sec4",
        "act": "Digital Personal Data Protection Act, 2023",
        "section": "Section 4",
        "citation": "Section 4, DPDP Act, 2023",
        "title": "Grounds for processing digital personal data",
        "category": "data_protection",
        "text": (
            "Section 4 establishes that personal data may only be processed for a lawful purpose for which the Data Principal has given or is "
            "deemed to have given consent in accordance with the Act, or for legitimate uses specified under Section 7. Contracts purporting to "
            "grant blanket, unconstrained rights to sell or monetize personal customer data violate statutory processing grounds."
        ),
    },
    {
        "id": "dpdp-sec6",
        "act": "Digital Personal Data Protection Act, 2023",
        "section": "Section 6",
        "citation": "Section 6, DPDP Act, 2023",
        "title": "Consent conditions and right to withdraw",
        "category": "data_protection",
        "text": (
            "Section 6 provides that consent given by a Data Principal must be free, specific, informed, unconditional, and unambiguous with a "
            "clear affirmative action. Any part of consent which infringes the provisions of this Act or the rules shall be invalid to the extent "
            "of such infringement. The Data Principal has the unconditional statutory right to withdraw consent at any time, and contracts cannot "
            "penalize or waive this right."
        ),
    },
    {
        "id": "dpdp-sec8",
        "act": "Digital Personal Data Protection Act, 2023",
        "section": "Section 8",
        "citation": "Section 8, DPDP Act, 2023",
        "title": "General obligations of Data Fiduciary",
        "category": "data_protection",
        "text": (
            "Section 8 mandates that a Data Fiduciary must implement reasonable security safeguards to prevent personal data breaches, notify the "
            "Data Protection Board and affected Data Principals in the event of any breach, and erase personal data as soon as the specified purpose "
            "has been served or consent is withdrawn. Clauses disclaiming data breach notification or retaining customer personal data in perpetuity "
            "directly contradict Section 8."
        ),
    },
]
