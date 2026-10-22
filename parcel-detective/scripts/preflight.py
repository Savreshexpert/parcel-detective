"""Real access probes; sends one small Bedrock request and one Decider request."""

import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parcel_detective.selector import DeciderSelector


def main():
    checks = []
    try:
        import boto3
        from botocore.config import Config

        region = os.getenv("AWS_REGION", "us-east-1")
        client = boto3.client("sts", region_name=region)
        # Verify credentials, but do not put account identity in the output.
        client.get_caller_identity()
        checks.append({"check": "AWS credentials", "ok": True})
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(
                connect_timeout=10, read_timeout=60, retries={"total_max_attempts": 1}
            ),
        )
        reply = bedrock.converse(
            modelId=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": "Reply with: Parcel Detective connection works."}
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 30, "temperature": 0},
        )
        checks.append({"check": "Bedrock Converse", "ok": bool(reply.get("output"))})
    except Exception as exc:
        checks.append({"check": "AWS / Bedrock", "ok": False, "error": str(exc)})
    try:
        base = os.getenv("DECIDER_URL", "http://127.0.0.1:8000")
        with urlopen(base.rstrip("/") + "/health", timeout=10) as response:
            health = json.loads(response.read())
        expected = os.getenv("DECIDER_MODEL", "strands-decider-2B-qwen3.5-v1-2610")
        selector = DeciderSelector(base, expected_model=expected)
        result = selector.select(
            {
                "parcel_id": "P104",
                "report": "The parcel has no dispatch scan.",
                "evidence": {},
            },
            {
                "scan_history": "Read parcel scanner events.",
                "handover_notes": "Read shift notes.",
            },
        )
        checks.append(
            {
                "check": "Decider typed-choice API",
                "ok": True,
                "model": result.model,
                "choice": result.tool,
                "confidence": result.confidence,
                "device": health.get("device"),
            }
        )
    except Exception as exc:
        checks.append(
            {"check": "Decider typed-choice API", "ok": False, "error": str(exc)}
        )
    print(
        json.dumps({"checks": checks, "ready": all(c["ok"] for c in checks)}, indent=2)
    )
    return 0 if all(c["ok"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
