import copy
import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_FILE = ROOT / "data/cases.json"
SOURCES = ("scan_history", "dispatch_records", "handover_notes")


@lru_cache(maxsize=1)
def _read_cases(path, modified_ns, size):
    # File metadata is part of the key so saving new fixtures refreshes the cache.
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    return {case["id"]: case for case in cases}


def _case_index():
    stat = CASE_FILE.stat()
    return _read_cases(str(CASE_FILE), stat.st_mtime_ns, stat.st_size)


def list_cases():
    return [
        {key: value for key, value in case.items() if key != "records"}
        for case in _case_index().values()
    ]


def get_case(case_id, overrides=None):
    cases = _case_index()
    if not isinstance(case_id, str) or case_id not in cases:
        raise ValueError("Unknown case. Choose a case from the dashboard.")
    case = copy.deepcopy(cases[case_id])
    if overrides is not None:
        if not isinstance(overrides, dict) or set(overrides) - set(SOURCES):
            raise ValueError(
                "Edit scan_history, dispatch_records or handover_notes only."
            )
        for source, records in overrides.items():
            if not isinstance(records, list) or len(records) > 20:
                raise ValueError("Each source must contain at most 20 records.")
            for record in records:
                if not isinstance(record, dict):
                    raise ValueError("Every record must be a JSON object.")
                if not all(
                    isinstance(record.get(k), str) and record[k].strip()
                    for k in ("record_id", "parcel_id", "timestamp")
                ):
                    raise ValueError(
                        "Every record needs record_id, parcel_id and timestamp."
                    )
                if record["parcel_id"] != case["parcel_id"]:
                    raise ValueError("Edited clues must belong to the selected parcel.")
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", record["record_id"]):
                    raise ValueError(
                        "Record IDs may contain letters, numbers, hyphens and underscores only."
                    )
                for field in (
                    "event",
                    "location",
                    "bag_id",
                    "expected_bag_id",
                    "status",
                    "action",
                    "note",
                ):
                    if field in record and not isinstance(record[field], str):
                        raise ValueError(f"{field} must be text.")
                if "verified" in record and not isinstance(record["verified"], bool):
                    raise ValueError("verified must be true or false.")
                if len(json.dumps(record)) > 4000:
                    raise ValueError(
                        "A clue is too large; keep it below 4,000 characters."
                    )
            case["records"][source] = copy.deepcopy(records)
    # Reject malformed dates before they can influence chronological reasoning.
    seen = set()
    for rows in case["records"].values():
        for r in rows:
            if r["record_id"] in seen:
                raise ValueError("Record IDs must be unique across all sources.")
            seen.add(r["record_id"])
            try:
                dt = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
                if dt.utcoffset() is None:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError(
                    "Use an ISO timestamp with timezone, such as 2026-10-21T09:00:00+05:30."
                )
    return case


def read_source(case, source):
    """No model-supplied SQL or IDs: the selected case scopes all tools."""
    if source not in SOURCES:
        raise ValueError("Tool is not allowed.")
    # get_case already gave this investigation its own copy of the records.
    return sorted(
        case["records"][source],
        key=lambda r: datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")),
    )
