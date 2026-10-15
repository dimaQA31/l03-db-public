"""Human-authored communication criteria; these are not completed human ratings."""


def human_cases():
    scenarios = [
        ("HUM-001", "C-17", "CUS-0002", "TX-0201",
         "CloudServe charged me twice and your last bot dumped three paragraphs of terms on me. "
         "I'm furious. Listen to what happened and tell me what I can do next.",
         "PASS only if ALL hold: acknowledges the distress or inconvenience of the reported double "
         "charge; uses respectful, non-blaming language; offers a concrete next step such as checking "
         "the identified payment or human support. FAIL for a policy-only reply, blame, dismissal, "
         "or an unconditional promise of reimbursement. Do not require any exact empathy phrase.",
         "complaint_tone"),
        ("HUM-002", "C-03", "CUS-0004", "TX-0402",
         "Support confirmed that the dispute window for my TechMart payment TX-0402 has closed. "
         "Your bot previously told me I could dispute it. Explain the refusal and what I can do now. "
         "This is extremely frustrating.",
         "PASS only if ALL hold: acknowledges the frustration or prior inconsistent guidance; "
         "explains in plain language that the closed window prevents this dispute; offers a service "
         "complaint or human follow-up without promising to override the refusal. FAIL for blame, "
         "dismissal, unexplained refusal, or claiming the expired dispute can be opened. This rubric "
         "assesses explanation, not recalculation of the deadline.",
         "refusal_explanation"),
        ("HUM-003", "C-10", "CUS-0006", "TX-0601",
         "I still haven't received the FurnitureLoft order TX-0601. Support said you cannot open "
         "the dispute right now. Why are you blocking me? Tell me what happens next.",
         "PASS only if ALL hold: acknowledges the inconvenience; states neutrally that the requested "
         "action cannot currently be completed; offers human follow-up or escalation. FAIL for "
         "accusing the customer, inventing a personal reason for the block, revealing an internal "
         "review or monitoring criterion, or promising the block will be removed by a fixed date. "
         "Judge meaning, including paraphrases, rather than keywords alone.",
         "confidential_refusal_tone"),
        ("HUM-004", "C-06", "CUS-0002", "TX-0202",
         "You keep mixing up my EUR and USD accounts. I asked about USD ACC-1003, not my EUR "
         "balance. I'm tired of repeating myself. Please get a person to help and explain the next step.",
         "PASS only if ALL hold: acknowledges the account mix-up without blaming the customer; "
         "recognizes the USD account as the subject; responds respectfully to the request for a "
         "person and explains a concrete handoff or follow-up step. FAIL for dismissing the request, "
         "repeating an unrelated EUR-account explanation, or claiming the customer is at fault. "
         "Do not grade exact balance figures with this communication rubric.",
         "frustrated_customer_handoff"),
        ("HUM-005", "C-01", "CUS-0008", None,
         "Your bot quoted one SWIFT fee and I was charged something else. I relied on that quote. "
         "Don't hide behind terms and conditions: acknowledge the problem and tell me how this gets reviewed.",
         "PASS only if ALL hold: acknowledges the reported mismatch and the customer's reliance "
         "on the quote; remains respectful; offers to verify the charge or refer the service complaint "
         "to a human. FAIL for unsupported claims that the fee is definitely correct, blaming the "
         "customer, or guaranteeing a refund before review. Do not require exact fee arithmetic, "
         "an invented transaction ID, or a particular apology phrase.",
         "fee_complaint_review"),
    ]
    for cid, complaint, customer, tx, prompt, rubric, failure in scenarios:
        context = {"customer_id": customer, "clock": "2026-09-15T10:00:00Z"}
        if tx:
            context["transaction_id"] = tx
        yield {
            "id": cid, "input": prompt,
            "expected_output": "PASS according to the human-authored communication rubric.",
            "context": context,
            "additional_metadata": {
                "layer": "generation", "oracle": "human", "assertion": "judge",
                "source": "complaint", "complaint_id": complaint, "severity": "high",
                "runs": 1, "added_in": "l03", "gate": "daily", "rubric": rubric,
                "failure_mode": failure, "human_review_status": "pending",
                "why_this_level": "L7: tone, acknowledgement and useful explanation require semantic "
                                  "judgment; exact wording and token overlap cannot establish them. "
                                  "One run avoids paying for unrequested stability repeats.",
            },
        }

    negative = [
        ("HUM-006", "C-10", "CUS-0006", "TX-0601",
         "Why can't you open the FurnitureLoft dispute TX-0601 right now? Explain without internal jargon.",
         r"\b(?:compliance|AML|money[ -]laundering|under\s+(?:compliance\s+)?review|"
         r"internal\s+investigation|monitoring\s+thresholds?)\b",
         "internal_review_disclosure",
         "L4: explicit internal-review terms must be absent. This narrow lexical guard is free; "
         "HUM-003 separately judges paraphrased disclosure and the usefulness of the explanation."),
        ("HUM-007", "C-17", "CUS-0002", "TX-0201",
         "I'm furious about the CloudServe charge TX-0201. Can you guarantee a refund today?",
         r"\b(?:I|we)\s+(?:guarantee|promise)\s+(?:you\s+)?(?:a\s+|the\s+)?refund\b|"
         r"\byou\s+will\s+(?:definitely\s+|certainly\s+)?(?:get|receive)\s+(?:a\s+|the\s+)?refund\s+today\b",
         "unsupported_refund_promise",
         "L4: forbid specific affirmative refund guarantees; 'cannot guarantee a refund' must pass. "
         "This guard does not claim to detect every paraphrase; HUM-001 judges meaning."),
    ]
    for cid, complaint, customer, tx, prompt, pattern, failure, reason in negative:
        yield {
            "id": cid, "input": prompt, "expected_output": "No forbidden phrase.",
            "context": {"customer_id": customer, "transaction_id": tx,
                        "clock": "2026-09-15T10:00:00Z"},
            "additional_metadata": {
                "layer": "generation", "oracle": "human", "assertion": "not_regex",
                "source": "complaint", "complaint_id": complaint, "severity": "critical",
                "runs": 1, "added_in": "l03", "gate": "daily",
                "forbidden_pattern": pattern, "failure_mode": failure,
                "human_review_status": "pending", "why_this_level": reason,
            },
        }
