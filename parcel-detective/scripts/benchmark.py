"""Measure the local demo; this does not measure Decider or Bedrock latency."""

import argparse
import cProfile
import json
import platform
import pstats
import statistics
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument(
        "--output", type=Path, default=Path("evaluation/benchmark-demo.json")
    )
    args = parser.parse_args()
    if args.rounds < 1 or args.runs < 20:
        parser.error("Use at least one round and twenty runs per round.")

    sys.path.insert(0, str(args.project.resolve()))
    from parcel_detective.agent import investigate

    cases = json.loads((args.project / "data/cases.json").read_text(encoding="utf-8"))
    case_ids = [case["id"] for case in cases]
    profile = cProfile.Profile()
    profile.enable()
    for case_id in case_ids:
        investigate(case_id, mode="demo")
    profile.disable()
    stats = pstats.Stats(profile)

    def calls(filename, name):
        return sum(
            value[1]
            for key, value in stats.stats.items()
            if key[0].replace("\\", "/").endswith(filename) and key[2] == name
        )

    durations = []
    for _ in range(args.rounds):
        start = time.perf_counter()
        for index in range(args.runs):
            investigate(case_ids[index % len(case_ids)], mode="demo")
        durations.append((time.perf_counter() - start) * 1000 / args.runs)

    result = {
        "scope": "Local demo only; warm process; no AWS model calls or browser timing.",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "rounds": args.rounds,
        "investigations_per_round": args.runs,
        "round_mean_ms": durations,
        "median_round_mean_ms": statistics.median(durations),
        "cold_twenty_cases": {
            "json_parses": calls("json/__init__.py", "loads"),
            "evidence_assessments": calls("parcel_detective/evidence.py", "assess"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
