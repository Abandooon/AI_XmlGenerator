"""Launch the patched loopback-only vLLM server from a frozen contract."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("contract_root_is_not_object")
    body = {key: item for key, item in value.items() if key != "content_sha256"}
    if value.get("content_sha256") != canonical_sha256(body):
        raise RuntimeError("contract_content_hash_mismatch")
    allowed = {
        "READY_FOR_QUALIFICATION",
        "READY_FOR_FORMAL_AFTER_EXPLICIT_AUTHORIZATION",
    }
    if value.get("decision") not in allowed:
        raise RuntimeError("contract_not_ready_for_server_launch")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_verified_document(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}_root_is_not_object")
    body = {key: item for key, item in value.items() if key != "content_sha256"}
    if value.get("content_sha256") != canonical_sha256(body):
        raise RuntimeError(f"{label}_content_hash_mismatch")
    return value


SPECULATIVE_ARGUMENT_PREFIXES = (
    "--speculative",
    "--num-speculative",
    "--draft-model",
)


def assert_no_speculative_decoding(
    contract: dict[str, Any], command: list[str]
) -> None:
    """Refuse to launch if anything here could enable speculative decoding.

    Speculative decoding is already prohibited in two places: the engine
    refuses to start when binding is required and num_speculative_tokens is
    non-zero (StructuredOutputManager.__init__), and a binding request is
    refused when a speculative config is present
    (SamplingParams._validate_spec_decode). This is the launch-side check, so
    the argument list this script builds cannot introduce one silently and the
    frozen contract and the launch cannot disagree. It deliberately sets no
    environment variable: nothing would read it, and a write-only variable
    reads like enforcement without being enforcement.
    """

    if contract["sampling"]["speculative_decoding"] is not False:
        raise RuntimeError("contract_does_not_declare_speculative_decoding_off")
    offending = [
        argument
        for argument in command
        if argument.startswith(SPECULATIVE_ARGUMENT_PREFIXES)
    ]
    if offending:
        raise RuntimeError(f"launch_introduces_speculative_decoding:{offending}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--runtime-fingerprint", type=Path, required=True)
    parser.add_argument("--overlay-manifest", type=Path, required=True)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--authorize-formal", action="store_true")
    args = parser.parse_args()
    contract = load_contract(args.contract.resolve())
    runtime_path = args.runtime_fingerprint.resolve()
    overlay_path = args.overlay_manifest.resolve()
    runtime = load_verified_document(runtime_path, "runtime_fingerprint")
    overlay = load_verified_document(overlay_path, "overlay_manifest")
    identities = {
        "runtime_fingerprint_file_sha256": sha256_file(runtime_path),
        "runtime_fingerprint_sha256": runtime["content_sha256"],
        "overlay_manifest_file_sha256": sha256_file(overlay_path),
        "overlay_manifest_content_sha256": overlay["content_sha256"],
    }
    for field_name, actual in identities.items():
        if contract.get(field_name) != actual:
            raise RuntimeError(f"contract_identity_mismatch:{field_name}")
    if runtime.get("decision") != "PASS" or overlay.get("decision") != "PASS":
        raise RuntimeError("runtime_or_overlay_not_admitted")
    if (
        contract["decision"] == "READY_FOR_FORMAL_AFTER_EXPLICIT_AUTHORIZATION"
        and not args.authorize_formal
    ):
        raise RuntimeError("formal_server_launch_requires_explicit_authorization")
    audit_root = args.audit_root.resolve()
    if audit_root.exists() and any(audit_root.iterdir()):
        raise FileExistsError(f"audit root is not empty: {audit_root}")
    audit_root.mkdir(parents=True, exist_ok=True)
    model_path = Path(contract["model_path"])
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    if metadata.version("vllm") != "0.26.0":
        raise RuntimeError("active_vllm_version_mismatch")
    required_launch_environment = contract.get("runtime_policy", {}).get(
        "required_environment"
    )
    if required_launch_environment != {"NCCL_CUMEM_HOST_ENABLE": "0"}:
        raise RuntimeError("contract_nccl_launch_environment_mismatch")
    vllm_executable_path = Path(sys.executable).resolve().parent / "vllm"
    vllm_executable = str(vllm_executable_path)
    if not vllm_executable_path.is_file():
        discovered = shutil.which("vllm")
        if discovered is None:
            raise RuntimeError("vllm_executable_not_found_in_active_environment")
        vllm_executable = discovered

    os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    for key, value in required_launch_environment.items():
        os.environ[key] = value
    os.environ["VLLM_STRUCTURED_OUTPUT_AUDIT_DIR"] = str(audit_root)
    os.environ["VLLM_STRUCTURED_OUTPUT_AUDIT_REQUIRED"] = "true"
    os.environ["VLLM_STRUCTURED_OUTPUT_BINDING_REQUIRED"] = "true"
    os.environ["VLLM_STRUCTURED_OUTPUT_AUDIT_QUEUE_SIZE"] = "65536"
    os.environ["VLLM_STRUCTURED_OUTPUT_EXPERIMENT_ID"] = contract[
        "experiment_id"
    ]
    os.environ["VLLM_STRUCTURED_OUTPUT_RUNTIME_FINGERPRINT_SHA256"] = contract[
        "runtime_fingerprint_sha256"
    ]
    os.environ["VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256"] = contract[
        "protocol_file_sha256"
    ]
    os.environ["VLLM_STRUCTURED_OUTPUT_ASSET_MANIFEST_SHA256"] = contract[
        "assets_manifest_content_sha256"
    ]

    command = [
        vllm_executable,
        "serve",
        str(model_path),
        "--served-model-name",
        contract["served_model_name"],
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--tensor-parallel-size",
        "2",
        "--dtype",
        "bfloat16",
        "--max-model-len",
        str(contract["max_model_len"]),
        "--max-num-seqs",
        "1",
        "--gpu-memory-utilization",
        "0.90",
        "--seed",
        "0",
        "--structured-outputs-config",
        json.dumps(
            {
                "backend": "xgrammar",
                "disable_any_whitespace": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        "--generation-config",
        "vllm",
        "--language-model-only",
        "--no-enable-prefix-caching",
        "--no-enable-log-requests",
        "--no-enable-log-outputs",
        "--disable-uvicorn-access-log",
        "--enable-request-id-headers",
    ]

    assert_no_speculative_decoding(contract, command)
    print(
        json.dumps(
            {
                "event": "atlas_vllm_launch_policy",
                "required_environment": required_launch_environment,
                "tensor_parallel_size": 2,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    os.execv(vllm_executable, command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
