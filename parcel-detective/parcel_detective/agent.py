import os
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from .records import SOURCES, get_case, read_source
from .evidence import assess, timestamp
from .selector import Decision, DemoSelector, DeciderSelector, allowed_tools
from .explainer import DemoExplainer, BedrockExplainer


@lru_cache(maxsize=2)
def components(mode):
    """Reuse provider clients; restart the server after changing AWS settings."""
    if mode == "demo":
        return DemoSelector(), DemoExplainer()
    if mode != "aws":
        raise ValueError("Mode must be demo or aws.")
    url = os.getenv("DECIDER_URL")
    if not url:
        raise ValueError("AWS mode needs DECIDER_URL. See docs/AWS_SETUP.md.")
    return (
        DeciderSelector(
            url,
            expected_model=os.getenv(
                "DECIDER_MODEL", "strands-decider-2B-qwen3.5-v1-2610"
            ),
        ),
        BedrockExplainer(),
    )


def investigate(case_id, overrides=None, mode="demo", selector=None, explainer=None):
    started = time.perf_counter()
    case = get_case(case_id, overrides)
    if selector is None or explainer is None:
        selector, explainer = components(mode)
    evidence, trace = {}, []
    selector_calls = 0
    for step in range(len(SOURCES)):
        choices = allowed_tools(evidence)
        # Single remaining options are host-enforced; never mislabel them model choices.
        if len(choices) == 1:
            decision = Decision(next(iter(choices)), None, "Host evidence policy", 0)
        else:
            decision = selector.select(
                {
                    "parcel_id": case["parcel_id"],
                    "report": case["report"],
                    "evidence": evidence,
                    "checked_sources": list(evidence),
                },
                choices,
            )
            selector_calls += 1
        if decision.tool not in choices:
            raise ValueError(
                "Selected tool is not allowed in the current investigation state."
            )
        entry = {
            "step": step + 1,
            "tool": decision.tool,
            "selector": decision.selector,
            "confidence": decision.confidence,
            "latency_ms": decision.latency_ms,
            "model": decision.model,
            "available_tools": list(choices),
            "probabilities": decision.probabilities,
        }
        rows = read_source(case, decision.tool)
        evidence[decision.tool] = rows
        entry["record_ids"] = [r["record_id"] for r in rows]
        trace.append(entry)
    finding = assess(case, evidence)
    terminal = allowed_tools(evidence, finding)
    trace.append(
        {
            "step": len(trace) + 1,
            "tool": next(iter(terminal)),
            "selector": "Host evidence policy",
            "confidence": None,
            "latency_ms": 0,
            "model": None,
            "available_tools": list(terminal),
            "probabilities": None,
            "record_ids": [],
        }
    )
    # When there are no records, a model cannot supply a real citation. Preserve
    # the factual evidence status and explicitly mark the no-record explanation.
    if not finding["supporting_record_ids"]:
        explanation = DemoExplainer().explain(finding, evidence)
        explanation["provider"] = "Host policy: no records to cite"
    else:
        explanation = explainer.explain(finding, evidence)
    timeline = sorted(
        [dict(r, source=source) for source, rows in evidence.items() for r in rows],
        key=timestamp,
    )
    physical = None
    if finding["physical_check_required"]:
        physical = {
            "status": "Prepared for worker — not sent",
            "location": finding["location"],
            "instructions": f"Check {case['parcel_id']} at {finding['location']}; compare its label with the bag manifest and record the actual location.",
            "record_ids": finding["supporting_record_ids"],
        }
    return {
        "run_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "fictional_data": True,
        "case_id": case_id,
        "parcel_id": case["parcel_id"],
        "clues_changed": bool(overrides),
        "finding": finding,
        "explanation": explanation,
        "timeline": timeline,
        "trace": trace,
        "physical_check": physical,
        "metrics": {
            "response_time_ms": round((time.perf_counter() - started) * 1000, 3),
            "evidence_tool_calls": len(evidence),
            "terminal_actions": 1,
            "decider_calls": selector_calls if mode == "aws" else 0,
            "demo_router_calls": selector_calls if mode == "demo" else 0,
            "bedrock_calls": explanation["bedrock_calls"],
            "record_count": len(timeline),
        },
    }
