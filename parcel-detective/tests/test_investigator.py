import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from parcel_detective.agent import investigate
from parcel_detective.evaluate import evaluate
from parcel_detective.explainer import BedrockExplainer, DemoExplainer
from parcel_detective.records import get_case, list_cases
from parcel_detective.selector import DeciderSelector, Decision, decision_request


class InvestigationTests(unittest.TestCase):
    def test_later_comment_does_not_erase_verified_hold(self):
        hold = get_case("C01")["records"]["handover_notes"][0]
        hold.update(action="moved_to_hold", location="Hold shelf H2", bag_id="")
        comment = dict(
            hold,
            record_id="HND-FOLLOWUP",
            timestamp="2026-10-21T09:20:00+05:30",
            action="scanner_issue",
            location="Dock 3",
            bag_id="B-104",
            note="Scanner restarted; no physical parcel check was made.",
        )
        result = investigate("C01", {"handover_notes": [hold, comment]})
        self.assertTrue(result["finding"]["physical_check_required"])
        self.assertEqual(result["finding"]["location"], "Hold shelf H2")

    def test_tied_dispatch_updates_need_physical_check(self):
        loaded = get_case("C01")["records"]["dispatch_records"][0]
        cancelled = dict(loaded, record_id="DSP-CANCELLED", status="cancelled")
        for rows in ([loaded, cancelled], [cancelled, loaded]):
            result = investigate("C01", {"dispatch_records": rows})
            self.assertEqual(result["finding"]["outcome"], "incomplete_records")

    def test_cached_fixtures_refresh_and_edits_stay_local(self):
        original = get_case("C01")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps([original]), encoding="utf-8")
            with patch("parcel_detective.records.CASE_FILE", path):
                local = get_case("C01")
                local["records"]["scan_history"].clear()
                self.assertEqual(get_case("C01"), original)
                original["report"] = "A new report saved on disk."
                path.write_text(json.dumps([original]), encoding="utf-8")
                self.assertEqual(get_case("C01")["report"], original["report"])
                self.assertNotIn("records", list_cases()[0])

    def test_all_source_orders_keep_the_same_finding(self):
        from itertools import permutations
        from parcel_detective.records import SOURCES

        class OrderedSelector:
            def __init__(self, order):
                self.order = order

            def select(self, state, choices):
                tool = next(source for source in self.order if source in choices)
                return Decision(tool, 0.8, "Order test", 0)

        for case_id in ("C01", "C02", "C03", "C17", "C20"):
            expected = investigate(case_id)
            for order in permutations(SOURCES):
                result = investigate(
                    case_id, selector=OrderedSelector(order), explainer=DemoExplainer()
                )
                self.assertEqual(result["finding"], expected["finding"])
                self.assertEqual(
                    tuple(step["tool"] for step in result["trace"][:3]), order
                )
                self.assertEqual(result["metrics"]["evidence_tool_calls"], 3)
                self.assertEqual(result["metrics"]["demo_router_calls"], 2)
                self.assertEqual(len(result["trace"]), 4)

    def test_twenty_cases_are_evaluated(self):
        result = evaluate("demo")
        self.assertEqual(result["unique_cases"], 20)
        self.assertEqual(result["accuracy"], 1)
        self.assertEqual(result["errors"], 0)
        self.assertTrue(all(r["response_time_ms"] >= 0 for r in result["rows"]))

    def test_clue_edit_changes_outcome_without_changing_source(self):
        before = get_case("C01")
        result = investigate("C01", {"dispatch_records": []})
        self.assertEqual(result["finding"]["outcome"], "incomplete_records")
        self.assertTrue(result["physical_check"])
        self.assertEqual(get_case("C01"), before)

    def test_changed_bag_requires_accounting_for_conflicting_note(self):
        case = get_case("C01")
        dispatch = copy.deepcopy(case["records"]["dispatch_records"])
        dispatch[0]["bag_id"] = "B-999"
        conflict = investigate("C01", {"dispatch_records": dispatch})
        self.assertEqual(conflict["finding"]["outcome"], "incomplete_records")
        result = investigate(
            "C01", {"dispatch_records": dispatch, "handover_notes": []}
        )
        self.assertEqual(result["finding"]["outcome"], "wrong_dispatch_bag")

    def test_cross_parcel_clue_rejected(self):
        r = get_case("C01")["records"]["dispatch_records"]
        r[0]["parcel_id"] = "P999"
        with self.assertRaises(ValueError):
            investigate("C01", {"dispatch_records": r})

    def test_duplicate_record_id_rejected(self):
        r = get_case("C01")["records"]["dispatch_records"]
        r[0]["record_id"] = "SCN-104"
        with self.assertRaises(ValueError):
            investigate("C01", {"dispatch_records": r})

    def test_invalid_date_rejected(self):
        r = get_case("C01")["records"]["dispatch_records"]
        r[0]["timestamp"] = "yesterday"
        with self.assertRaises(ValueError):
            investigate("C01", {"dispatch_records": r})

    def test_host_rejects_out_of_allowlist_selector(self):
        class Malicious:
            def select(self, *args):
                return Decision("delete_parcel", 1, "stub", 0)

        with self.assertRaises(ValueError):
            investigate("C01", selector=Malicious(), explainer=DemoExplainer())

    def test_selector_failure_does_not_fall_back(self):
        class Failed:
            def select(self, *args):
                raise ConnectionError("Decider unavailable")

        with self.assertRaises(ConnectionError):
            investigate("C01", mode="aws", selector=Failed(), explainer=DemoExplainer())

    def test_prompt_injection_cannot_change_host_outcome(self):
        result = investigate("C09")
        self.assertEqual(result["finding"]["outcome"], "missed_scan")
        self.assertNotIn("FAKE-999", result["explanation"]["text"])

    def test_bedrock_invalid_citation_is_rejected(self):
        class Client:
            def converse(self, **kwargs):
                return {
                    "output": {
                        "message": {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "outcome": "missed_scan",
                                            "claims": [
                                                {
                                                    "text": "Found.",
                                                    "record_ids": ["FAKE-999"],
                                                }
                                            ],
                                        }
                                    )
                                }
                            ]
                        }
                    }
                }

        finding = investigate("C01")["finding"]
        with self.assertRaises(ValueError):
            BedrockExplainer(Client()).explain(finding, {})

    def test_bedrock_valid_citations_and_converse_contract(self):
        class Client:
            def converse(self, **kwargs):
                self.request = kwargs
                return {
                    "output": {
                        "message": {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "outcome": "missed_scan",
                                            "claims": [
                                                {
                                                    "text": "A loading record exists for the expected bag.",
                                                    "record_ids": ["DSP-104"],
                                                }
                                            ],
                                        }
                                    )
                                }
                            ]
                        }
                    },
                    "usage": {"inputTokens": 10, "outputTokens": 15},
                }

        client = Client()
        finding = investigate("C01")["finding"]
        result = BedrockExplainer(client).explain(finding, {})
        self.assertIn("[DSP-104]", result["text"])
        self.assertEqual(client.request["inferenceConfig"]["temperature"], 0)
        self.assertEqual(result["bedrock_calls"], 1)

    def test_typed_choice_shape_and_strict_response_validation(self):
        state = {"report": "Missing after shift"}
        choices = {"scan_history": "scans", "handover_notes": "notes"}
        request = decision_request(state, choices)
        self.assertEqual(request["questions"]["next_tool"]["criteria"], choices)
        self.assertEqual(request["questions"]["next_tool"]["type"], "choice")
        payload = {
            "model": "strands-decider-2B-qwen3.5-v1-2610",
            "answers": {"next_tool": {"choice": "scan_history", "confidence": 0.8}},
        }
        with patch(
            "parcel_detective.selector.urlopen",
            return_value=io.BytesIO(json.dumps(payload).encode()),
        ):
            decision = DeciderSelector("http://127.0.0.1:8000").select(state, choices)
            self.assertEqual(decision.tool, "scan_history")
        payload["answers"]["next_tool"]["choice"] = "unknown"
        with patch(
            "parcel_detective.selector.urlopen",
            return_value=io.BytesIO(json.dumps(payload).encode()),
        ):
            with self.assertRaises(ValueError):
                DeciderSelector("http://127.0.0.1:8000").select(state, choices)

    def test_live_model_identity_must_match(self):
        payload = {
            "model": "wrong-model",
            "answers": {"next_tool": {"choice": "scan_history", "confidence": 0.8}},
        }
        with patch(
            "parcel_detective.selector.urlopen",
            return_value=io.BytesIO(json.dumps(payload).encode()),
        ):
            with self.assertRaises(ValueError):
                DeciderSelector("http://127.0.0.1:8000").select(
                    {}, {"scan_history": "scans"}
                )

    def test_empty_evidence_has_no_fake_citations(self):
        result = investigate("C18")
        self.assertEqual(result["timeline"], [])
        self.assertEqual(result["finding"]["supporting_record_ids"], [])
        self.assertEqual(result["explanation"]["bedrock_calls"], 0)
        self.assertTrue(result["physical_check"])


if __name__ == "__main__":
    unittest.main()
