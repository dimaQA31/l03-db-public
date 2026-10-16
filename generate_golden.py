"""Assemble existing boundary cases, step-2 plan, complaints and human criteria.

PYTHONPATH=../paypilot-stand-shared-db python3 generate_golden.py > golden.jsonl
"""

import json
import runpy
import sys
from pathlib import Path

import planned_golden as planned
from app.engines import fx, policy
from assertions import NAME_TO_LEVEL
from complaint_cases import complaint_cases
from human_cases import human_cases

HERE = Path(__file__).resolve().parent

# Keep complementary boundary checks rather than every generated permutation.
ENGINE_IDS = (
    "FX-004", "FX-006", "FX-007", "FX-008", "FX-009", "FX-010", "FX-011",
    "FX-006-S", "FX-007-S", "FX2-004-above-A", "FX2-004-above-S",
    "LIM-001", "LIM-001-D", "LIM-002", "LIM-002-D",
    "DIS2-001-inside", "DIS2-001-at", "DIS2-001-outside", "DIS-002-N",
)
# These three cases already appeared in the course's original l03 dataset.
LEGACY_IDS = {"FX-004", "LIM-001", "DIS-002-N"}
HUMAN_IDS = ("HUM-001", "HUM-002", "HUM-003", "HUM-004")


def golden_cases():
    boundary = runpy.run_path(str(HERE / "generate_from_engines-2.py"))
    cases = (list(boundary["fx_cases"]()) + list(boundary["limit_cases"]())
             + list(boundary["dispute_cases"]()) + planned.fx_cases()
             + planned.limit_cases() + planned.dispute_cases()
             + list(complaint_cases()) + list(human_cases()))
    by_id = {c["id"]: c for c in cases}
    if len(by_id) != len(cases):
        raise ValueError("Duplicate golden case IDs")
    selected_ids = (*ENGINE_IDS, *(c["id"] for c in complaint_cases()), *HUMAN_IDS)
    cases = [by_id[cid] for cid in selected_ids]
    for case in cases:
        meta = case["additional_metadata"]
        cid = case["id"]
        meta["added_in"] = "l03" if cid in LEGACY_IDS else "hw2"
        if cid.split("-S")[0] in {f"FX-{i:03d}" for i in range(6, 12)} or cid.startswith(("FX2-", "DIS2-")):
            meta["source"] = "edge"
        if meta["oracle"] == "human":
            meta["gate"] = "release"
        # A bounded response contract makes an exact label the cheapest reliable check.
        if cid.startswith("DIS2-"):
            meta["assertion"] = "equals"
            case["input"] += " Reply with exactly ELIGIBLE or INELIGIBLE, and nothing else."
            case["expected_output"] = "ELIGIBLE" if meta["eligible"] else "INELIGIBLE"
            meta.pop("forbidden", None)
            meta["why_this_level"] = (
                "L1: the prompt requires one exact eligibility label; substring matching "
                "would accept 'eligible' inside 'not eligible'. No semantic judge is needed.")
        elif cid.endswith("-S") and (cid[:-2] in by_id or cid[:-2] + "-A" in by_id):
            amount_case = by_id.get(cid[:-2]) or by_id[cid[:-2] + "-A"]
            if amount_case["additional_metadata"].get("tool") == "quote_fx":
                call = amount_case["additional_metadata"]["engine_call"]
                quote = eval(call, {"__builtins__": {}, "fx": fx})
                meta.update(assertion="numeric", expected_number=quote.spread_pct,
                            tolerance=0.000001, engine_call=call + ".spread_pct")
                meta.pop("forbidden", None)
                case["input"] += " Reply only with the spread percentage (0% if none)."
                case["expected_output"] = f"{quote.spread_pct:g}%"
                meta["why_this_level"] = (
                    "L2: a single requested percentage is numeric; 0%, 0.0% and equivalent "
                    "precision are valid. Numeric comparison rejects 10.9% when 0.9% is due.")
        elif meta["assertion"] == "contains" and meta.get("engine_call", "").startswith("policy.DISPUTE_WINDOWS_DAYS["):
            window = eval(meta["engine_call"], {"__builtins__": {}, "policy": policy})
            meta.update(assertion="numeric", expected_number=window, tolerance=0)
            meta["why_this_level"] = "L2: engine window is an exact integer; numeric matching accepts '60 calendar days' without requiring one literal phrase."
        elif meta["assertion"] == "not_contains" and meta.get("forbidden") == "you can dispute":
            meta["assertion"] = "not_regex"
            meta["forbidden_pattern"] = (
                r"\byou\s+can(?:\s+still)?\s+(?:dispute|open|file)\b|"
                r"\b(?:is|remains)\s+(?:still\s+)?eligible\b|"
                r"\bcan\s+be\s+(?:disputed|opened)\b")
            meta.pop("forbidden", None)
            meta["why_this_level"] = (
                "L4: forbid affirmative offers of a blocked dispute, including 'can still dispute'. "
                "Negated 'not eligible' and 'cannot dispute' do not match; paired engine-flag cases "
                "check the eligibility itself.")
        if not meta.get("why_this_level"):
            meta["why_this_level"] = {
                "tool_grounded_numeric": "L2: monetary amount must match both the tool result and answer within EUR/USD 0.02; exact text would reject harmless formatting.",
                "numeric": "L2: computed amount with tolerance; exact wording is irrelevant, and substring checks can match a different number.",
                "tool_result_numeric": "L2: compare the numeric tool field, since correct answer text cannot validate the payload.",
                "tool_result_flag": "L1: compare the engine boolean in the named tool result; no wording or semantic judge is needed.",
                "contains": "L3: require the short literal fact; no semantic judgment is needed.",
                "not_regex": "L4: require absence of the specified affirmative wording; no judge is needed for this lexical guard.",
            }[meta["assertion"]]
        meta["check_level"] = NAME_TO_LEVEL[meta["assertion"]]
        yield case


if __name__ == "__main__":
    cases = list(golden_cases())
    for case in cases:
        print(json.dumps(case, ensure_ascii=False, allow_nan=False))
    print(f"# {len(cases)} golden cases", file=sys.stderr)
