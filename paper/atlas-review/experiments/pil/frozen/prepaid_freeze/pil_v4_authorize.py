"""Convert a passing PIL V4 preflight into a separate formal-run authorization.

This command makes no provider calls and never edits the frozen preflight.  It
requires the same explicit token as the paid runner so authorization is a
deliberate, separately timestamped event.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pil_v4_contract as contract
import pil_v4_provider
import pil_v4_schedule


ROOT = Path(__file__).resolve().parent
PAID_CONFIRMATION = contract.PAID_CONFIRMATION


def _load_verified_preflight(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"preflight manifest missing: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    declared = document.get("content_sha256")
    content = {
        key: value
        for key, value in document.items()
        if key not in {"created_at_utc", "content_sha256"}
    }
    if declared != contract.canonical_sha256(content):
        raise ValueError("preflight content hash mismatch")
    blockers = pil_v4_schedule.readiness_blockers(
        path, require_execution_authorization=False,
    )
    if blockers:
        raise ValueError("preflight is blocked:\n- " + "\n- ".join(blockers))
    if document.get("status") != "READY_FOR_PAID_AUTHORIZATION":
        raise ValueError("preflight status is not READY_FOR_PAID_AUTHORIZATION")
    if document.get("prepaid_blockers"):
        raise ValueError("preflight still declares blockers")
    if document.get("provider_calls") != 0 or document.get("paid_api_calls") != 0:
        raise ValueError("preflight is not a zero-call artifact")
    return document


def build_formal_readiness(
    preflight_path: Path,
    confirmation: str,
    api_base: str = "",
) -> dict[str, Any]:
    if confirmation != PAID_CONFIRMATION:
        raise ValueError(f"authorization requires confirmation token {PAID_CONFIRMATION}")
    preflight = _load_verified_preflight(preflight_path)
    normalized_api_base = pil_v4_provider.normalize_base_url(api_base)
    timestamp = datetime.now(timezone.utc).isoformat()
    body = {
        "schema_version": "atlas.pil.formal_readiness.v4.1",
        "created_at_utc": timestamp,
        "status": "READY_FOR_FORMAL_RUN",
        "formal_run_enabled": True,
        "external_calls_authorized": True,
        "provider_calls_before_authorization": 0,
        "paid_api_calls_before_authorization": 0,
        "authorization": {
            "authorized_at_utc": timestamp,
            "authorized_unit_count": 720,
            "confirmation_token_sha256": contract.canonical_sha256(PAID_CONFIRMATION),
            "preflight_file_sha256": contract.sha256_file(preflight_path),
            "preflight_content_sha256": preflight["content_sha256"],
            "preflight_path": str(preflight_path),
            "api_base_sha256": hashlib.sha256(
                normalized_api_base.encode("utf-8")
            ).hexdigest(),
        },
        "review": preflight["review"],
        "inputs": preflight["inputs"],
        "implementation": preflight["implementation"],
        "provider_contract": preflight["provider_contract"],
        "runtime_environment": preflight["runtime_environment"],
        "required_checks": preflight["required_checks"],
        "summary": preflight["summary"],
        "scope_limits": preflight["scope_limits"],
    }
    stable = {
        key: value for key, value in body.items()
        if key not in {"created_at_utc"}
    }
    return {**body, "content_sha256": contract.canonical_sha256(stable)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight", type=Path, default=ROOT / "PIL_V41_PREFLIGHT_READINESS.json",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "PIL_V41_FORMAL_READINESS.json",
    )
    parser.add_argument("--confirm-paid-run", default="")
    parser.add_argument(
        "--api-base", default="",
        help="Provider base URL to bind by hash; defaults to the configured V4 endpoint.",
    )
    args = parser.parse_args(argv)
    api_base = args.api_base or pil_v4_provider.configured_base_url()
    document = build_formal_readiness(
        args.preflight, args.confirm_paid_run, api_base,
    )
    if args.output.exists():
        raise ValueError(f"refusing to overwrite existing authorization: {args.output}")
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "status": document["status"],
        "authorized_unit_count": document["authorization"]["authorized_unit_count"],
        "provider_calls": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
