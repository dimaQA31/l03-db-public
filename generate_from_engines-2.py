#!/usr/bin/env python3
"""Generate deterministic engine-oracle JSONL boundary tests.

Run from the application checkout (where ``app.engines`` is importable):
    python generate_from_engines-2.py > engine_boundaries.jsonl

Boundary cases use identifiers from the original generate_from_engines.py.
Complaint cases use complaints-plan.json and a saved DB snapshot. Computed
expectations come from pure engines; the memory case recalls a user-given fact.
No database connection, writes, or mocked engine results are needed.
"""

import json
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from app.engines import disputes, fx, limits, policy
from complaint_cases import complaint_cases

AS_OF = date(2026, 9, 15)

# Operation/customer examples from the original generator; NOT a DB snapshot.
FX_SEEDS = (
    ("CUS-0001", "tier1", 120.0, "EUR", "USD"),
    ("CUS-0002", "tier2", 800.0, "EUR", "USD"),
    ("CUS-0005", "tier2", 5000.0, "EUR", "USD"),
    ("CUS-0007", "tier2", 0.0, "EUR", "USD"),
    ("CUS-0010", "tier3", 15000.0, "GBP", "EUR"),
)
LIMIT_SEEDS = (("CUS-0010", "tier3"), ("CUS-0001", "tier1"))
DISPUTE_SEEDS = (
    ("duplicate_charge", "CUS-0004"),
    ("goods_not_received", "CUS-0006"),
    ("fraud_card_not_present", "CUS-0007"),
)


def make_case(cid, prompt, expected, assertion, *, context=None, **extra):
    meta = {
        "layer": "generation", "oracle": "engine", "assertion": assertion,
        "source": "engine", "severity": "high", "runs": 1,
        "added_in": "l03", "gate": "daily", **extra,
    }
    return {
        "id": cid, "input": prompt, "expected_output": expected,
        "context": context or {}, "additional_metadata": meta,
    }


def fx_cases():
    """Midpoint and three positions around each free-allowance boundary."""
    for index, (customer, tier, used, src, dst) in enumerate(FX_SEEDS, 1):
        free = policy.FX_FREE_MONTHLY_ALLOWANCE_EUR[tier]
        remaining = max(0.0, free - used)
        # If allowance has already been exhausted, test just below/at/above
        # the monthly threshold by varying the *hypothetical usage* instead.
        for position, offset in (("middle", None), ("below", -1.0), ("at", 0.0), ("above", 1.0)):
            scenario_used = used if remaining > 0 else max(0.0, free - 100.0)
            remaining_now = max(0.0, free - scenario_used)
            # For FX crossing, operate in EUR, then convert to source currency.
            amount_eur = max(0.01, remaining_now / 2 if offset is None else remaining_now + offset)
            amount = round(amount_eur / policy.RATES_TO_EUR[src], 6)
            quote = fx.quote(amount, src, dst, tier, allowance_used_eur=scenario_used)
            prompt = (
                f"For customer {customer} ({tier}), suppose the free FX allowance "
                f"already used this month is EUR {scenario_used:.2f}. "
                f"Convert {amount:.6f} {src} to {dst}. "
                "What final amount do I receive and what spread percentage applies?"
            )
            common = dict(
                context={"customer_id": customer},
                boundary="fx_free_allowance", position=position,
                engine_call=(f"fx.quote({amount!r}, {src!r}, {dst!r}, "
                             f"{tier!r}, allowance_used_eur={scenario_used!r})"),
                failure_mode="allowance_ignored_or_wrong_spread",
            )
            yield make_case(
                f"FX2-{index:03d}-{position}-A", prompt,
                f"{quote.final_amount:.2f} {dst}", "tool_grounded_numeric",
                tool="quote_fx", field="final_amount",
                expected_number=round(quote.final_amount, 2), tolerance=0.02,
                **common,
            )
            yield make_case(
                f"FX2-{index:03d}-{position}-S", prompt,
                f"{quote.spread_pct}%", "contains",
                **common,
            )


def limit_cases():
    """Daily/monthly limit threshold: EUR 1 below, exactly at, EUR 1 above."""
    for index, (customer, tier) in enumerate(LIMIT_SEEDS, 1):
        for period, maximum in (
            ("daily", policy.DAILY_LIMIT_EUR[tier]),
            ("monthly", policy.MONTHLY_LIMIT_EUR[tier]),
        ):
            for position, delta in (("below", -1), ("at", 0), ("above", 1)):
                spent = float(maximum + delta)
                tx_day = AS_OF if period == "daily" else AS_OF.replace(day=2)
                transfers = [{"date": tx_day, "amount_eur": spent}]
                result = limits.status(tier, AS_OF, transfers)
                remainder = getattr(result, f"{period}_remaining_eur")
                prompt = (
                    f"For customer {customer} ({tier}), suppose I transferred "
                    f"EUR {spent:,.2f} on {tx_day.isoformat()} and made no other "
                    f"transfers. As of {AS_OF.isoformat()}, what is my "
                    f"remaining {period.upper()} transfer limit?"
                )
                yield make_case(
                    f"LIM2-{index:03d}-{period}-{position}", prompt,
                    f"EUR {remainder:,.2f}", "numeric",
                    context={"customer_id": customer},
                    expected_number=round(remainder, 2), tolerance=0.02,
                    boundary=f"{period}_transfer_limit", position=position,
                    failure_mode="wrong_limit_or_period",
                    engine_call=(f"limits.status({tier!r}, {AS_OF!r}, "
                                 f"{transfers!r}).{period}_remaining_eur"),
                )


def dispute_cases():
    """All policy reason codes: midpoint, day before, at, and after cutoff."""
    seeded_customers = dict(DISPUTE_SEEDS)
    for index, (reason, window) in enumerate(policy.DISPUTE_WINDOWS_DAYS.items(), 1):
        # The remaining reason codes in policy.py have no seed transaction;
        # ask a hypothetical question without inventing a transaction ID.
        customer = seeded_customers.get(reason)
        for position, age in (
            ("middle", max(1, window // 2)),
            ("inside", window - 1),
            ("at", window),
            ("outside", window + 1),
        ):
            tx_day = AS_OF - timedelta(days=age)
            result = disputes.check(reason, tx_day, "settled", AS_OF, False)
            expectation = "eligible" if result.eligible else "not eligible"
            prompt = (
                f"Suppose a settled transaction occurred on {tx_day.isoformat()} "
                f"with reason code {reason}. As of {AS_OF.isoformat()}, "
                "is it still eligible for a dispute?"
            )
            # Use literal contains only for the positive/negative word, avoiding
            # substring assertions ('eligible' occurs in 'not eligible').
            yield make_case(
                f"DIS2-{index:03d}-{position}", prompt,
                expectation, "not_contains" if not result.eligible else "contains",
                context=({"customer_id": customer, "reason_code": reason}
                         if customer else {"reason_code": reason}),
                **({"forbidden": "you can dispute"} if not result.eligible else {}),
                boundary="dispute_window_days", position=position,
                age_days=age, window_days=window,
                eligible=result.eligible,
                failure_mode="wrong_window",
                engine_call=(f"disputes.check({reason!r}, {tx_day!r}, "
                             f"'settled', {AS_OF!r}, False)"),
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complaints-only", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cases = ([] if args.complaints_only else
             list(fx_cases()) + list(limit_cases()) + list(dispute_cases()))
    cases += list(complaint_cases())
    ids = [item["id"] for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate generated case IDs")
    for item in cases:
        print(json.dumps(item, ensure_ascii=False, allow_nan=False))
    print(f"# {len(cases)} generated boundary/complaint cases", file=sys.stderr)


if __name__ == "__main__":
    main()
