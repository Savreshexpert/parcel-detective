"""Conservative rules over retrieved records; no evaluation answers are imported."""

from datetime import datetime
from .records import SOURCES


def timestamp(record):
    return datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))


def assess(case, evidence):
    scans = evidence.get("scan_history", [])
    dispatch = evidence.get("dispatch_records", [])
    notes = evidence.get("handover_notes", [])
    last_scan = max(scans, key=timestamp, default=None)
    last_dispatch = max(dispatch, key=timestamp, default=None)
    verified_notes = [n for n in notes if n.get("verified") is True]
    last_note = max(verified_notes, key=timestamp, default=None)
    # Every source must have been checked. The first version deliberately favours
    # completeness; Decider selects order, but we do not claim reduced tool count.
    complete = all(source in evidence for source in SOURCES)
    result = {
        "outcome": "incomplete_records",
        "label": "Physical check needed",
        "location": (last_scan or {}).get("location") or "last receiving area",
        "supporting_record_ids": [],
        "physical_check_required": True,
        "reason": "The available records do not establish a reliable next location.",
        "sources_complete": complete,
    }
    rows = scans + dispatch + notes
    if not complete:
        result["reason"] = "Some evidence sources have not been checked yet."
        return result
    result["supporting_record_ids"] = [r["record_id"] for r in rows]
    if not last_scan or not last_dispatch:
        return result
    dispatch_time = timestamp(last_dispatch)
    latest_assignments = {
        (row.get("status"), row.get("bag_id"), row.get("expected_bag_id"))
        for row in dispatch
        if timestamp(row) == dispatch_time
    }
    if len(latest_assignments) > 1:
        result["reason"] = (
            "Equally recent dispatch records disagree about the parcel's bag or loading status."
        )
        return result
    if last_dispatch.get("status") != "loaded" or not last_dispatch.get("bag_id"):
        result["reason"] = (
            "No active loaded-bag record establishes the parcel's next location."
        )
        return result
    # A later conflicting scan or verified handover invalidates a dispatch inference.
    bag = last_dispatch["bag_id"]
    conflicting_scans = [
        row
        for row in scans
        if timestamp(row) >= dispatch_time
        and (
            row.get("event") in ("RETURN", "HOLD")
            or (row.get("bag_id") and row["bag_id"] != bag)
        )
    ]
    conflicting_notes = [
        row
        for row in verified_notes
        if timestamp(row) >= dispatch_time
        and (
            row.get("action") == "moved_to_hold"
            or (row.get("bag_id") and row["bag_id"] != bag)
        )
    ]
    if conflicting_scans or conflicting_notes:
        # A later general comment does not undo an unresolved physical hold.
        latest_conflict = max(conflicting_scans + conflicting_notes, key=timestamp)
        if latest_conflict.get("location"):
            result["location"] = latest_conflict["location"]
        result["reason"] = (
            "A later record conflicts with the dispatch record; a worker must verify the location."
        )
        return result
    expected = last_dispatch.get("expected_bag_id")
    if not expected:
        result["reason"] = (
            "The dispatch record has no expected bag, so the route cannot be verified."
        )
        return result
    result.update(
        location=f"bag {bag} at {last_dispatch.get('location') or 'dispatch staging'}",
        supporting_record_ids=list(
            dict.fromkeys(
                [last_scan["record_id"], last_dispatch["record_id"]]
                + ([last_note["record_id"]] if last_note else [])
            )
        ),
    )
    if bag != expected:
        result.update(
            outcome="wrong_dispatch_bag",
            label="Wrong dispatch bag suspected",
            physical_check_required=False,
            reason=f"The active loading record names bag {bag}; the expected bag is {expected}.",
        )
    elif not any(
        s.get("event") == "DISPATCH"
        and s.get("bag_id") == bag
        and timestamp(s) >= dispatch_time
        for s in scans
    ):
        result.update(
            outcome="missed_scan",
            label="Missed scan suspected",
            physical_check_required=False,
            reason="The parcel is in an active loading record for the expected bag, but no matching dispatch scan is recorded.",
        )
    else:
        result["reason"] = (
            "Dispatch and scans agree; the missing-parcel alert needs a physical verification."
        )
    return result
