"""Synthetic ledger boundary tests. No model or native verifier is executed."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("extension_independent_review", Path(__file__).with_name("verify_final.py"))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
previous, old, _ = review.helpers(review.BASE)
prior_path = review.BASE / "continuation2/run/BUDGET.jsonl"


class ExtensionReviewTests(unittest.TestCase):
    def setUp(self):
        self.events = previous.read_budget_lines(prior_path)
        self.approval, self.amendment = "1" * 64, "2" * 64

    def append(self, item):
        event = {"sequence": len(self.events) + 1, "previous": self.events[-1]["hash"],
                 "utc": "2026-09-10T00:00:00+00:00", **item}
        self.events.append({**event, "hash": old.identity(event)})

    def extend(self, **overrides):
        item = {"kind": review.CAP_EVENT, "key": "GLOBAL_BUDGET_CAP", "old_cap_nano": 5_000_000_000,
                "new_cap_nano": 6_000_000_000, "occupied_nano": 3_916_463_250,
                "user_explicit_total_cap_usd": 6, "approval_sha256": self.approval,
                "amendment_sha256": self.amendment, "historical_unknown_occupied_nano": 2_187_456_000,
                "missing_response_replacements_added": 0}
        self.append({**item, **overrides})

    def reserve(self, key="CONTINUATION3/BAL-3-01/G0/shared_initial"):
        self.append({"kind": "RESERVE", "key": key, "cap_nano": 6_000_000_000,
                     "reserved_nano": previous.RESERVATION, "input_tokens_reserved": 272000,
                     "output_tokens_reserved": 4096, "occupied_after_nano": 5_010_191_250})

    def unknown(self):
        self.append({"kind": "UNKNOWN", "key": "CONTINUATION3/BAL-3-01/G0/shared_initial",
                     "occupied_nano": previous.RESERVATION, "usage": None})

    def run_ledger(self):
        prefix = prior_path.read_bytes()
        count = len(previous.read_budget_lines(prior_path))
        suffix = "".join(old.canonical(event) + "\n" for event in self.events[count:]).encode("utf-8")
        with tempfile.TemporaryDirectory(prefix="atlas_extension_review_") as directory:
            path = Path(directory) / "synthetic_ledger.jsonl"
            path.write_bytes(prefix + suffix)
            return review.replay_extension(path, prior_path, previous, old, self.approval, self.amendment)

    def test_extension_does_not_release_unknowns_or_add_request(self):
        self.extend()
        entries, _, _, _, new_keys = self.run_ledger()
        self.assertEqual(len(entries), 60)
        self.assertEqual(new_keys, [])
        self.assertEqual(sum(e["occupied"] for e in entries.values()), 3_916_463_250)
        self.assertEqual(sum(entries[k]["occupied"] for k in previous.UNKNOWN_KEYS), 2_187_456_000)

    def test_cap_extension_requires_explicit_six_dollars(self):
        self.extend(user_explicit_total_cap_usd=5)
        with self.assertRaisesRegex(ValueError, "authorization"):
            self.run_ledger()

    def test_cap_extension_cannot_release_old_occupancy(self):
        self.extend(occupied_nano=0)
        with self.assertRaisesRegex(ValueError, "authorization"):
            self.run_ledger()

    def test_cap_change_is_not_an_unknown_response_replacement(self):
        self.extend(missing_response_replacements_added=1)
        with self.assertRaisesRegex(ValueError, "authorization"):
            self.run_ledger()

    def test_no_reservation_before_extension(self):
        self.reserve()
        self.unknown()
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            self.run_ledger()

    def test_only_last_task_admitted(self):
        self.extend()
        self.reserve("CONTINUATION3/BAL-1-01/G0/shared_initial")
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            self.run_ledger()

    def test_new_unknown_remains_reserved_and_blocks_more_calls(self):
        self.extend()
        self.reserve()
        self.unknown()
        entries, _, _, _, new_keys = self.run_ledger()
        self.assertEqual(len(new_keys), 1)
        self.assertEqual(sum(e["occupied"] for e in entries.values()), 5_010_191_250)
        self.reserve("CONTINUATION3/BAL-3-01/GS/round_01")
        with self.assertRaisesRegex(ValueError, "unresolved"):
            self.run_ledger()

    def test_second_cap_event_rejected(self):
        self.extend()
        self.extend()
        with self.assertRaisesRegex(ValueError, "repeated"):
            self.run_ledger()


if __name__ == "__main__":
    unittest.main(verbosity=2)
