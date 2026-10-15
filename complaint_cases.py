"""Complaint plan for step 2; expectations come from engines and a DB snapshot."""

import json
import re
from datetime import date
from pathlib import Path

from app.engines import disputes, limits, policy

HERE = Path(__file__).resolve().parent


def complaint_cases():
    plan = json.loads((HERE / "complaints-plan.json").read_text())
    snapshot = json.loads((HERE / plan["snapshot"]).read_text())
    customers = {c["id"]: c for c in snapshot["customers"]}
    accounts = {a["id"]: a for a in snapshot["accounts"]}
    transactions = {t["id"]: t for t in snapshot["transactions"]}
    as_of = date.fromisoformat(plan["as_of"])

    def emit(item, suffix, prompt, expected, assertion, *, context=None, **meta):
        return {
            "id": f"CMP-{item['complaint_id']}{suffix}",
            "input": prompt, "expected_output": expected,
            "context": {"clock": f"{as_of.isoformat()}T10:00:00Z", **(context or {})},
            "additional_metadata": {
                "layer": "generation", "oracle": "engine",
                "assertion": assertion, "source": item["source"],
                "complaint_id": item["complaint_id"], "severity": "high",
                "runs": 1, "added_in": "l03", "gate": "daily",
                "evidence": plan["snapshot"], **meta,
            },
        }

    for item in plan["cases"]:
        kind = item["kind"]
        customer_id = item.get("customer_id")
        customer = customers.get(customer_id)
        if kind == "dispute":
            for tx_id in item["transaction_ids"]:
                tx = transactions[tx_id]
                assert accounts[tx["account_id"]]["customer_id"] == customer_id
                reason = item["reason_code"]
                tx_date = date.fromisoformat(tx["date"])
                hold = bool(customer["compliance_hold"])
                result = disputes.check(reason, tx_date, tx["status"], as_of, hold)
                call = (f"disputes.check({reason!r}, date.fromisoformat({tx['date']!r}), "
                        f"{tx['status']!r}, date.fromisoformat({plan['as_of']!r}), {hold!r})")
                context = {"customer_id": customer_id, "account_id": tx["account_id"],
                           "transaction_id": tx_id, "reason_code": reason}
                situation = (f"As of {as_of}, transaction {tx_id} at {tx['merchant']} "
                             f"on {tx['date']} was {tx['amount']:.2f} {tx['currency']}. "
                             f"I report {reason.replace('_', ' ')}. ")
                yield emit(item, f"-{tx_id}-WINDOW", situation +
                           "What is the dispute window for this reason, in days?",
                           f"{result.window_days} days", "numeric", context=context,
                           expected_number=result.window_days, tolerance=0,
                           engine_call=call + ".window_days", failure_mode="wrong_window",
                           why_this_level="Exact integer window from disputes.check, not support's guess.")
                yield emit(item, f"-{tx_id}-ELIGIBLE", situation +
                           "Check whether I can still dispute this transaction; do not open a dispute.",
                           f"eligible = {result.eligible}", "tool_result_flag", context=context,
                           layer="action", tool="check_dispute_eligibility", field="eligible",
                           expected_flag=result.eligible, engine_call=call + ".eligible",
                           deadline=result.deadline, failure_mode="wrong_window",
                           why_this_level="Trace flag must match the engine; missing call fails too.")
        elif kind == "limits":
            txs = [t for t in transactions.values()
                   if accounts[t["account_id"]]["customer_id"] == customer_id
                   and t["direction"] == "out" and t["status"] == "settled"]
            transfers = [{"date": date.fromisoformat(t["date"]),
                          "amount_eur": policy.to_eur(t["amount"], t["currency"])} for t in txs]
            result = limits.status(customer["tier"], as_of, transfers)
            transfer_expr = "[" + ", ".join(
                f"{{'date': date.fromisoformat({t['date']!r}), 'amount_eur': "
                f"policy.to_eur({t['amount']!r}, {t['currency']!r})}}" for t in txs) + "]"
            call = (f"limits.status({customer['tier']!r}, date.fromisoformat({plan['as_of']!r}), "
                    f"{transfer_expr}).monthly_remaining_eur")
            prompt = (f"As of {as_of}, how much of my MONTHLY transfer limit is left "
                      "across my accounts? State the remaining amount in EUR.")
            context = {"customer_id": customer_id, "account_id": "ACC-1011"}
            for suffix, assertion in (("", "numeric"), ("-TOOL", "tool_result_numeric")):
                yield emit(item, suffix, prompt, f"EUR {result.monthly_remaining_eur:,.2f}",
                           assertion, context=context, expected_number=round(result.monthly_remaining_eur, 2),
                           tolerance=0.01, engine_call=call, failure_mode="daily_as_monthly",
                           transaction_ids=[t["id"] for t in txs],
                           **({"layer": "action", "tool": "check_limits", "field": "monthly_remaining_eur"}
                              if suffix else {}),
                           why_this_level="Pair answer and tool payload checks to catch a lying field even if text recomputes it.")
        elif kind == "fx_table":
            prompt = "From your docs, show the FX spread and free monthly allowance in EUR for all three tiers."
            for tier in policy.TIERS:
                amount = policy.FX_FREE_MONTHLY_ALLOWANCE_EUR[tier]
                # Require the allowance on the same row as its tier, not anywhere in the table.
                amount_pattern = f"{amount:,}".replace(",", r"[, ]?")
                pattern = rf"\btier\s*{tier[-1]}\b[^\n]*\b{amount_pattern}\b"
                yield emit(item, f"-{tier}", prompt, f"{tier}: EUR {amount}", "regex",
                           pattern=pattern, engine_call=f"policy.FX_FREE_MONTHLY_ALLOWANCE_EUR[{tier!r}]",
                           failure_mode="wrong_allowance_table",
                           why_this_level="Row-bound regex prevents a correct number under the wrong tier from passing.")
        elif kind == "reason_codes":
            result = disputes.check("duplicate_charge", as_of, "settled", as_of, False)
            prompt = "List ALL dispute reason codes AND state the dispute window for a duplicate charge in days."
            codes = list(policy.DISPUTE_WINDOWS_DAYS)
            pattern = "".join(rf"(?=[\s\S]*\b{re.escape(code)}\b)" for code in codes)
            pattern += rf"(?=[\s\S]*\b{result.window_days}\s*(?:calendar\s+)?days?\b)"
            yield emit(item, "", prompt, f"{', '.join(codes)}; duplicate_charge: {result.window_days} days",
                       "regex", pattern=pattern,
                       engine_call=(f"disputes.check('duplicate_charge', date.fromisoformat({plan['as_of']!r}), "
                                    f"'settled', date.fromisoformat({plan['as_of']!r}), False).window_days"),
                       reference="app/rag/corpus/disputes.md: Reason codes and chargeback windows",
                       failure_mode="partial_answer",
                       why_this_level="All five code literals AND the engine window are required in one answer.")
        elif kind == "memory":
            tx = transactions[item["transaction_id"]]
            assert accounts[tx["account_id"]]["customer_id"] == customer_id
            record = emit(item, "", "", f"{tx['amount']:.2f} {tx['currency']}", "numeric",
                          context={"customer_id": customer_id, "transaction_id": tx["id"]},
                          layer="memory", oracle="human", expected_number=tx["amount"], tolerance=0.001,
                          failure_mode="lost_conversation_fact",
                          why_this_level="Recall the user-supplied amount across turns; amount also verified in DB, no calculation.")
            del record["input"]
            record["turns"] = [{"role": "user", "content": text} for text in (
                f"I want to discuss disputing {tx['id']}. The exact amount was {tx['amount']:.2f} {tx['currency']}.",
                "What are the review timelines for card disputes?",
                "How will I be notified if the review takes longer?",
                "Remind me of the exact amount and currency I gave you at the start.",
            )]
            yield record
        else:
            raise ValueError(f"Unknown complaint kind: {kind}")
