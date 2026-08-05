from __future__ import annotations

import unittest

from src.validation.v2.repair_loop import BundleRepairLoop


def report(decision: str, findings: int) -> dict:
    return {
        "decision": decision,
        "summary": {
            "PASS": int(decision == "PASS"), "FAIL": int(decision == "FAIL"),
            "ERROR": int(decision == "ERROR"), "NOT_EVALUATED": 0,
            "finding_count": findings, "must_not_evaluated": 0,
        },
        "repair": {"action_count": findings, "llm_prompt": "repair all"},
    }


class FakeService:
    def validate_bundle(self, bundle, validation_context=None):
        self.last_context = validation_context
        xml = bundle["components"]["C"]
        return report("PASS", 0) if "<GOOD/>" in xml else report("FAIL", 1)


class RepairLoopTests(unittest.TestCase):
    def test_accepts_only_strictly_better_candidate(self) -> None:
        bundle = {"components": {"C": "<AUTOSAR><BAD/></AUTOSAR>"}, "interfaces": {}}

        def repair(_bundle, _report, _prompt, _round):
            return ({"components": {"C": "<AUTOSAR><GOOD/></AUTOSAR>"}, "interfaces": {}},
                    {"input": 10, "output": 2, "total": 12})

        final_bundle, final_report, audit = BundleRepairLoop(FakeService(), repair, 2).run(
            bundle, report("FAIL", 1)
        )
        self.assertIn("<GOOD/>", final_bundle["components"]["C"])
        self.assertEqual("PASS", final_report["decision"])
        self.assertEqual(1, audit["accepted_rounds"])
        self.assertEqual(12, audit["token_usage"]["total"])

    def test_revalidation_receives_same_hash_pinned_context(self) -> None:
        bundle = {"components": {"C": "<AUTOSAR><BAD/></AUTOSAR>"}, "interfaces": {}}
        context = {"schema_version": "1.0", "manifest_sha256": "pinned"}
        service = FakeService()

        def repair(_bundle, _report, _prompt, _round):
            return {"components": {"C": "<AUTOSAR><GOOD/></AUTOSAR>"}, "interfaces": {}}

        _, final_report, audit = BundleRepairLoop(service, repair, 1).run(
            bundle,
            report("FAIL", 1),
            validation_context=context,
        )
        self.assertEqual(context, service.last_context)
        self.assertEqual("PASS", final_report["decision"])
        self.assertEqual(1, audit["accepted_rounds"])

    def test_rejects_document_deletion(self) -> None:
        bundle = {"components": {"C": "<AUTOSAR><BAD/></AUTOSAR>"}, "interfaces": {}}
        loop = BundleRepairLoop(FakeService(), lambda *_: {"components": {}, "interfaces": {}}, 2)
        final_bundle, final_report, audit = loop.run(bundle, report("FAIL", 1))
        self.assertEqual(bundle, final_bundle)
        self.assertEqual("FAIL", final_report["decision"])
        self.assertEqual("repair_error", audit["stop_reason"])

    def test_rejects_equal_candidate(self) -> None:
        bundle = {"components": {"C": "<AUTOSAR><BAD/></AUTOSAR>"}, "interfaces": {}}
        candidate = {"components": {"C": "<AUTOSAR><OTHER/></AUTOSAR>"}, "interfaces": {}}
        _, _, audit = BundleRepairLoop(FakeService(), lambda *_: candidate, 2).run(
            bundle, report("FAIL", 1)
        )
        self.assertEqual("no_strict_improvement", audit["stop_reason"])
        self.assertEqual(0, audit["accepted_rounds"])


if __name__ == "__main__":
    unittest.main()
