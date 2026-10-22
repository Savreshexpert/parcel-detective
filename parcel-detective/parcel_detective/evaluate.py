import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from .agent import investigate
from .records import ROOT


def evaluate(mode="demo", repeats=1):
    truth_path = ROOT / "evaluation/ground_truth.json"
    truth = json.loads(truth_path.read_text())
    rows = []
    for repeat in range(repeats):
        for expected in truth:
            try:
                result = investigate(expected["case_id"], mode=mode)
                finding = result["finding"]
                correct = (
                    finding["outcome"] == expected["outcome"]
                    and finding["physical_check_required"]
                    == expected["physical_check_required"]
                    and all(
                        word in finding["location"]
                        for word in expected["location_contains"]
                    )
                )
                rows.append(
                    {
                        "case_id": expected["case_id"],
                        "repeat": repeat + 1,
                        "expected": expected["outcome"],
                        "actual": finding["outcome"],
                        "correct": correct,
                        "citation_ids_valid": result["explanation"]["citations_valid"],
                        "explanation_provider": result["explanation"]["provider"],
                        **result["metrics"],
                        "error": None,
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "case_id": expected["case_id"],
                        "repeat": repeat + 1,
                        "expected": expected["outcome"],
                        "actual": "error",
                        "correct": False,
                        "citation_ids_valid": False,
                        "response_time_ms": None,
                        "evidence_tool_calls": None,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    times = sorted(
        r["response_time_ms"] for r in rows if r["response_time_ms"] is not None
    )
    return {
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Synthetic development fixtures; not a held-out benchmark. Demo results do not measure AI accuracy.",
        "ground_truth_sha256": hashlib.sha256(truth_path.read_bytes()).hexdigest(),
        "records_sha256": hashlib.sha256(
            (ROOT / "data/cases.json").read_bytes()
        ).hexdigest(),
        "unique_cases": len(truth),
        "runs": len(rows),
        "repeats": repeats,
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "errors": sum(bool(r["error"]) for r in rows),
        "median_response_ms": statistics.median(times) if times else None,
        "p95_response_ms": times[math.ceil(0.95 * len(times)) - 1] if times else None,
        "mean_evidence_tool_calls": (
            statistics.mean(
                r["evidence_tool_calls"]
                for r in rows
                if r["evidence_tool_calls"] is not None
            )
            if times
            else None
        ),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "aws"], default="demo")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("repeats must be between 1 and 10")
    result = evaluate(args.mode, args.repeats)
    path = Path(args.output or f"evaluation/results-{args.mode}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    fields = list(dict.fromkeys(k for r in result["rows"] for k in r))
    with path.with_suffix(".csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["rows"])
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    raise SystemExit(0 if result["accuracy"] == 1 and not result["errors"] else 1)


if __name__ == "__main__":
    main()
