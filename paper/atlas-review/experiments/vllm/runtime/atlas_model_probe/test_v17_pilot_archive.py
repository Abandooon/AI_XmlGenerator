from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path


DOCUMENTS = Path(r"E:\54239\Documents")
ARCHIVE = DOCUMENTS / "ATLAS_V17_PILOT_ARCHIVE_2026-08-25_6a182944"
LIVE_ROOT = (
    DOCUMENTS
    / "atlas_model_probe"
    / "outputs"
    / "luna-main-asw-v3-v17-20260825-formal"
)
INCIDENT_ARCHIVE = (
    DOCUMENTS
    / "ATLAS_V17_INFRASTRUCTURE_INCIDENT_ARCHIVE_2026-08-25_7685d99e_WIN10013_11of60"
)
INCIDENT_LIVE_ROOT = (
    DOCUMENTS
    / "atlas_model_probe"
    / "outputs"
    / "luna-main-asw-v3-v17-20260825-formal-7685d99e-primary"
)
REGISTRY = Path(
    r"E:\git projects\AI_XmlGenerator\config\atlas_experiment_registry.json"
)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_hashed(path: Path) -> dict:
    body = json.loads(path.read_text(encoding="utf-8"))
    content_sha256 = body.pop("content_sha256")
    if canonical_sha256(body) != content_sha256:
        raise AssertionError(f"canonical content hash mismatch: {path}")
    body["content_sha256"] = content_sha256
    return body


class V17PilotArchiveTests(unittest.TestCase):
    def test_original_batch_is_recoverable_and_the_live_duplicate_is_gone(self):
        manifest = load_hashed(ARCHIVE / "ARCHIVE_MANIFEST.json")
        archive_path = ARCHIVE / manifest["original_batch_zip"]
        self.assertEqual(
            manifest["original_batch_zip_sha256"], sha256_file(archive_path)
        )
        expected = {item["path"]: item for item in manifest["source_files"]}
        self.assertEqual(manifest["source_file_count"], len(expected))
        with zipfile.ZipFile(archive_path, "r") as archive:
            self.assertEqual(set(expected), set(archive.namelist()))
            for name in archive.namelist():
                payload = archive.read(name)
                self.assertEqual(expected[name]["size_bytes"], len(payload), name)
                self.assertEqual(
                    expected[name]["sha256"],
                    hashlib.sha256(payload).hexdigest(),
                    name,
                )
        self.assertFalse(LIVE_ROOT.exists())

    def test_batch_is_wholly_excluded_and_registry_hashes_bind_the_archive(self):
        manifest = load_hashed(ARCHIVE / "ARCHIVE_MANIFEST.json")
        batch = load_hashed(ARCHIVE / "BATCH_STATUS.json")
        incident = load_hashed(ARCHIVE / "TRANSPORT_INCIDENT_REPORT.json")
        probe = load_hashed(
            ARCHIVE / "qualification_probe" / "QUALIFICATION_PROBE_STATUS.json"
        )
        self.assertEqual(23, batch["completed_slots"])
        self.assertEqual(37, batch["not_started_slots"])
        self.assertEqual(
            {
                "AMBIGUOUS_PROVIDER_DELIVERY": 5,
                "MODEL_OR_SCHEMA_GENERATION_FAILURE": 1,
                "SUCCESSFUL_ARTIFACT": 17,
            },
            batch["completion_kinds"],
        )
        self.assertFalse(batch["admissible_to_primary_results"])
        self.assertFalse(batch["resume_permitted"])
        self.assertEqual(
            "UNRESOLVED_TIME_CLUSTERED_TRANSPORT_FAILURE",
            incident["incident_class"],
        )
        self.assertEqual("UNKNOWN", batch["ambiguous_call_billing"])
        self.assertEqual("UNKNOWN", probe["failed_call_billing"])
        self.assertEqual(7, probe["provider_calls"])
        self.assertEqual(42742, probe["confirmed_response_usage_tokens_lower_bound"])

        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        autosar = registry["experiments"]["autosar"]
        self.assertEqual("V17-candidate", autosar["active_code_line"])
        self.assertEqual("NOT_RUN", autosar["active_result_status"])
        entry = next(
            item
            for item in autosar["aborted_pilots"]
            if item["id"] == "E1-V17-PILOT-6a182944"
        )
        self.assertTrue(entry["archive_only"])
        self.assertFalse(entry["admissible_to_paper_tables"])
        self.assertEqual(
            manifest["content_sha256"], entry["archive_manifest_content_sha256"]
        )
        self.assertEqual(
            batch["content_sha256"], entry["batch_status_content_sha256"]
        )
        self.assertEqual(
            incident["content_sha256"],
            entry["transport_incident_report_content_sha256"],
        )
        self.assertEqual(
            probe["content_sha256"],
            entry["qualification_probe_status_content_sha256"],
        )

    def test_probe_archive_contains_no_literal_credential(self):
        for name in ("atlas_transport_probe.py", "transport_probe_results.json"):
            text = (ARCHIVE / "qualification_probe" / name).read_text(
                encoding="utf-8"
            ).lower()
            for forbidden in ('"api_key": "', "authorization: bearer", "sk-"):
                self.assertNotIn(forbidden, text)


class V17RestrictedLaunchIncidentArchiveTests(unittest.TestCase):
    def test_original_batch_is_recoverable_and_live_duplicate_is_gone(self):
        manifest = load_hashed(INCIDENT_ARCHIVE / "ARCHIVE_MANIFEST.json")
        archive_path = INCIDENT_ARCHIVE / manifest["original_batch_zip"]
        self.assertEqual(
            manifest["original_batch_zip_sha256"], sha256_file(archive_path)
        )
        expected = {item["path"]: item for item in manifest["source_files"]}
        self.assertEqual(106, manifest["source_file_count"])
        self.assertEqual(manifest["source_file_count"], len(expected))
        with zipfile.ZipFile(archive_path, "r") as archive:
            self.assertEqual(set(expected), set(archive.namelist()))
            for name in archive.namelist():
                payload = archive.read(name)
                self.assertEqual(expected[name]["size_bytes"], len(payload), name)
                self.assertEqual(
                    expected[name]["sha256"],
                    hashlib.sha256(payload).hexdigest(),
                    name,
                )
                lowered = payload.lower()
                for forbidden in (b'"api_key": "', b"authorization: bearer", b"sk-"):
                    self.assertNotIn(forbidden, lowered, name)
        self.assertFalse(INCIDENT_LIVE_ROOT.exists())

    def test_incident_is_wholly_excluded_and_registry_hashes_bind_archive(self):
        manifest = load_hashed(INCIDENT_ARCHIVE / "ARCHIVE_MANIFEST.json")
        batch = load_hashed(INCIDENT_ARCHIVE / "BATCH_STATUS.json")
        incident = load_hashed(INCIDENT_ARCHIVE / "TRANSPORT_INCIDENT_REPORT.json")
        self.assertEqual(11, batch["completed_slots"])
        self.assertEqual(49, batch["not_started_slots"])
        self.assertEqual(
            {"AMBIGUOUS_PROVIDER_DELIVERY": 11}, batch["completion_kinds"]
        )
        self.assertEqual("UNKNOWN", batch["ambiguous_call_billing"])
        self.assertEqual(0, batch["provider_responses_locally_audited"])
        self.assertEqual(0, batch["provider_calls_interrupted"])
        self.assertFalse(batch["admissible_to_primary_results"])
        self.assertFalse(batch["resume_permitted"])
        self.assertEqual(
            "LOCAL_EXECUTION_ENVIRONMENT_SOCKET_PERMISSION_DENIED",
            incident["incident_class"],
        )

        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        autosar = registry["experiments"]["autosar"]
        self.assertEqual("NOT_RUN", autosar["active_result_status"])
        entry = next(
            item
            for item in autosar["aborted_pilots"]
            if item["id"] == "E1-V17-PRIMARY-ABORT-7685d99e-WIN10013"
        )
        self.assertTrue(entry["archive_only"])
        self.assertFalse(entry["admissible_to_paper_tables"])
        self.assertFalse(entry["resume_permitted"])
        self.assertEqual(
            manifest["original_batch_zip_sha256"], entry["archive_zip_sha256"]
        )
        self.assertEqual(
            manifest["content_sha256"], entry["archive_manifest_content_sha256"]
        )
        self.assertEqual(
            batch["content_sha256"], entry["batch_status_content_sha256"]
        )
        self.assertEqual(
            incident["content_sha256"],
            entry["transport_incident_report_content_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
