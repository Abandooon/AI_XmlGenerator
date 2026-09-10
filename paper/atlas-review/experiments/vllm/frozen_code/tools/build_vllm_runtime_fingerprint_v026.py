"""Build a hash-pinned runtime fingerprint on the Ubuntu GPU host."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(arguments: list[str]) -> str:
    return subprocess.check_output(
        arguments,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def gpu_topology_probe(gpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Capture topology without hiding the managed-container hwloc defect.

    The matrix is informational. A known post-reboot cpuset/hwloc failure may
    be recorded only under the same exact signature as preflight; the separate
    two-rank NCCL all-reduce remains a mandatory contract gate.
    """

    completed = subprocess.run(
        ["nvidia-smi", "topo", "-m"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    combined = "\n".join(part for part in (stdout, stderr) if part)
    evidence: dict[str, Any] = {
        "command": ["nvidia-smi", "topo", "-m"],
        "returncode": int(completed.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "output": combined,
        "gpu_uuids": [str(gpu.get("uuid")) for gpu in gpus],
    }
    if completed.returncode == 0:
        evidence.update({"decision": "PASS", "mode": "matrix"})
        return evidence

    status_lines = {}
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith(("Cpus_allowed", "Mems_allowed")):
            key, value = line.split(":", 1)
            status_lines[key] = value.strip()
    cpuset_path = Path("/sys/fs/cgroup/cpuset.cpus.effective")
    online_path = Path("/sys/devices/system/cpu/online")
    degraded_errors = []
    for signature in (
        "Topology does not contain any PU",
        "Failed to run topology matrix",
    ):
        if signature not in combined:
            degraded_errors.append(f"missing_signature:{signature}")
    gpu_uuids = evidence["gpu_uuids"]
    if len(gpu_uuids) != 2 or len(set(gpu_uuids)) != 2:
        degraded_errors.append("expected_two_distinct_gpu_uuids")
    if not cpuset_path.is_file() or not cpuset_path.read_text().strip():
        degraded_errors.append("cgroup_cpuset_effective_missing")
    if not online_path.is_file() or not online_path.read_text().strip():
        degraded_errors.append("kernel_online_cpus_missing")
    if not status_lines:
        degraded_errors.append("proc_self_status_affinity_missing")
    evidence.update(
        {
            "decision": "PASS" if not degraded_errors else "FAIL",
            "mode": "known_hwloc_cpuset_degradation",
            "degraded_errors": degraded_errors,
            "proc_self_status_affinity": status_lines,
            "cgroup_cpuset_effective": (
                cpuset_path.read_text(encoding="utf-8").strip()
                if cpuset_path.is_file()
                else None
            ),
            "kernel_online_cpus": (
                online_path.read_text(encoding="utf-8").strip()
                if online_path.is_file()
                else None
            ),
            "requires_nccl_tp2_gate": True,
        }
    )
    return evidence


def model_file_manifest(model_path: Path) -> list[dict[str, Any]]:
    files = sorted(path for path in model_path.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError("model_directory_is_empty")
    return [
        {
            "path": path.relative_to(model_path).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]


def gpu_inventory() -> list[dict[str, Any]]:
    raw = command_output(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    records = []
    for line in raw.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 5:
            raise RuntimeError("unexpected_nvidia_smi_inventory_format")
        records.append(
            {
                "index": int(fields[0]),
                "name": fields[1],
                "uuid": fields[2],
                "memory_total_mib": int(fields[3]),
                "driver_version": fields[4],
            }
        )
    return records


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


REQUIRED_TASK_FREE_BYTES = 35 * 1024**3


def filesystem_errors(
    *, model_free_bytes: int, task_free_bytes: int
) -> list[str]:
    """Gate on the filesystem the experiment writes to, and only that one.

    Results, audit traces, and compiled assets are written under the task root.
    Nothing is ever written into the model directory, and model libraries are
    frequently read-only mounts that report zero or meaningless free space, so
    gating on the model filesystem would fail a perfectly deployable instance.
    The model filesystem is recorded; the task filesystem is what decides, and
    it is the same filesystem preflight checks.
    """

    errors = []
    if task_free_bytes < REQUIRED_TASK_FREE_BYTES:
        errors.append("task_filesystem_free_space_is_below_35gib")
    return errors


TRACKED_DISTRIBUTIONS = (
    "apache-tvm-ffi",
    "torch",
    "vllm",
    "xgrammar",
    "transformers",
    "tokenizers",
    "safetensors",
    "numpy",
)


def _installed_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def speculative_guard_probe() -> dict[str, Any]:
    """Demonstrate both speculative prohibitions against the installed vLLM.

    Binding observation reads the pre-mask argmax of a decode step. Under
    speculative decoding the observed step may be a proposal that is later
    rejected, and this overlay establishes no proposed-to-accepted mapping, so
    the row could not be attributed to an emitted token. Two independent guards
    prohibit the combination, and both are exercised here:

      engine level   StructuredOutputManager.__init__ refuses to construct when
                     binding is required and num_speculative_tokens is non-zero
      request level  SamplingParams._validate_spec_decode refuses a binding
                     request when a speculative config is present

    Neither check starts an engine, allocates a backend, opens an audit file,
    starts a writer thread, or issues a model call. The engine-level guard runs
    before the audit sink is constructed, and the request-level guard is a pure
    validation method. Those absences are asserted here, not assumed.

    A skip is not an outcome. Anything other than the expected behaviour -- an
    import failure, a missing exception, an unexpected exception, the wrong
    error identity, or a side effect on the rejection path -- is a failure,
    because a guard that cannot be demonstrated on the target host has not been
    shown to exist on the target host.
    """

    results: dict[str, Any] = {"checks": {}, "errors": []}

    def record(name: str, ok: bool, detail: str = "") -> None:
        results["checks"][name] = {"pass": ok, "detail": detail}
        if not ok:
            results["errors"].append(f"speculative_guard_{name}:{detail}"[:200])

    try:
        from vllm.sampling_params import SamplingParams, StructuredOutputsParams
    except Exception as exc:  # noqa: BLE001 - the import outcome is the datum
        record("request_level_import", False, f"{type(exc).__name__}:{exc}")
        return results
    record("request_level_import", True)

    def sampling(binding: bool) -> Any:
        return SamplingParams(
            temperature=0.0,
            structured_outputs=StructuredOutputsParams(
                json_object=True,
                atlas_audit_binding=binding,
                atlas_audit_request_id=(
                    "atlas-uga-guard-probe-request" if binding else None
                ),
            ),
        )

    # A non-None sentinel is sufficient: the guard branches on presence, not on
    # the contents of the speculative config.
    speculative_present = object()

    try:
        sampling(binding=True)._validate_spec_decode(speculative_present)
    except ValueError as exc:
        expected = "atlas_audit_binding is not supported" in str(exc)
        record("request_level_refuses_binding", expected, str(exc)[:160])
    except Exception as exc:  # noqa: BLE001
        record("request_level_refuses_binding", False, type(exc).__name__)
    else:
        record("request_level_refuses_binding", False, "no exception raised")

    try:
        sampling(binding=True)._validate_spec_decode(None)
        record("request_level_allows_without_speculative", True)
    except Exception as exc:  # noqa: BLE001
        record(
            "request_level_allows_without_speculative",
            False,
            f"{type(exc).__name__}:{exc}",
        )

    try:
        sampling(binding=False)._validate_spec_decode(speculative_present)
        record("request_level_ignores_non_binding", True)
    except Exception as exc:  # noqa: BLE001
        record(
            "request_level_ignores_non_binding",
            False,
            f"{type(exc).__name__}:{exc}",
        )

    # The engine-level guard is the load-bearing one, so it is exercised
    # directly rather than inferred from the request-level result.
    try:
        from vllm.v1.structured_output import StructuredOutputManager
        from vllm.v1.structured_output.audit import StructuredOutputAuditError
    except Exception as exc:  # noqa: BLE001
        record("engine_level_import", False, f"{type(exc).__name__}:{exc}")
        return results
    record("engine_level_import", True)

    class _SpeculativeConfigStub:
        num_speculative_tokens = 1

    # The audit directory is pointed at a path that does not exist yet.
    # Constructing the audit sink would create it and start a daemon writer
    # thread, and the rejection path leaves no handle through which such a
    # thread could be closed. The guard therefore runs before the sink is
    # built, and this probe asserts that absence of side effects rather than
    # assuming it.
    with tempfile.TemporaryDirectory() as audit_parent:
        audit_dir = Path(audit_parent) / "audit"
        environment = {
            "VLLM_STRUCTURED_OUTPUT_BINDING_REQUIRED": "true",
            "VLLM_STRUCTURED_OUTPUT_AUDIT_REQUIRED": "true",
            "VLLM_STRUCTURED_OUTPUT_AUDIT_DIR": str(audit_dir),
            "VLLM_STRUCTURED_OUTPUT_EXPERIMENT_ID": "atlas-uga-guard-probe",
            "VLLM_STRUCTURED_OUTPUT_RUNTIME_FINGERPRINT_SHA256": "0" * 64,
            "VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256": "0" * 64,
            "VLLM_STRUCTURED_OUTPUT_ASSET_MANIFEST_SHA256": "0" * 64,
        }
        saved = {key: os.environ.get(key) for key in environment}
        threads_before = threading.active_count()
        try:
            os.environ.update(environment)
            try:
                StructuredOutputManager(_SpeculativeConfigStub())
            except StructuredOutputAuditError as exc:
                # Compare the error identity, not merely the exception type:
                # the same exception class also carries the audit-sink guard.
                expected = (
                    str(exc) == "binding_requires_speculative_decoding_disabled"
                )
                record("engine_level_refuses_binding", expected, str(exc)[:160])
            except Exception as exc:  # noqa: BLE001
                record(
                    "engine_level_refuses_binding",
                    False,
                    f"{type(exc).__name__}:{exc}"[:160],
                )
            else:
                record(
                    "engine_level_refuses_binding", False, "no exception raised"
                )
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        record(
            "engine_level_allocates_no_audit_directory",
            not audit_dir.exists(),
            f"unexpected audit directory at {audit_dir}",
        )

    record(
        "engine_level_starts_no_writer_thread",
        threading.active_count() == threads_before,
        f"thread count {threads_before} -> {threading.active_count()}",
    )

    return results


def build_fingerprint(
    *,
    model_path: Path,
    task_root: Path,
    overlay_manifest_path: Path,
) -> dict[str, Any]:
    model_path = model_path.resolve()
    task_root = task_root.resolve()
    overlay_manifest_path = overlay_manifest_path.resolve()
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    if not task_root.is_dir():
        raise FileNotFoundError(f"task root does not exist: {task_root}")
    import torch
    import vllm
    import xgrammar

    gpus = gpu_inventory()
    topology_probe = gpu_topology_probe(gpus)
    system_memory_bytes = int(command_output(["getconf", "_PHYS_PAGES"])) * int(
        command_output(["getconf", "PAGE_SIZE"])
    )
    shared_memory_bytes = shutil.disk_usage("/dev/shm").total
    model_filesystem = shutil.disk_usage(model_path)
    task_filesystem = shutil.disk_usage(task_root)
    errors: list[str] = list(
        filesystem_errors(
            model_free_bytes=model_filesystem.free,
            task_free_bytes=task_filesystem.free,
        )
    )
    if topology_probe["decision"] != "PASS":
        errors.append("gpu_topology_probe_not_admitted")
    if sys.version_info[:2] != (3, 12):
        errors.append("python_is_not_3_12")
    if metadata.version("vllm") != "0.26.0":
        errors.append("vllm_is_not_0_26_0")
    if metadata.version("xgrammar") != "0.2.6rc1":
        errors.append("xgrammar_is_not_0_2_6rc1")
    if metadata.version("apache-tvm-ffi") != "0.1.10":
        errors.append("apache_tvm_ffi_is_not_0_1_10")
    if metadata.version("transformers") != "5.16.1":
        errors.append("transformers_is_not_5_16_1")
    if not metadata.version("torch").startswith("2.11."):
        errors.append("torch_is_not_2_11")
    if not str(torch.version.cuda or "").startswith("13.0"):
        errors.append("torch_cuda_build_is_not_cu130")
    if len(gpus) != 2:
        errors.append("gpu_count_is_not_two")
    if any("RTX 4090" not in gpu["name"] for gpu in gpus):
        errors.append("gpu_model_is_not_rtx_4090")
    if any(gpu["memory_total_mib"] < 23_000 for gpu in gpus):
        errors.append("gpu_memory_is_below_23gb")
    if system_memory_bytes < 64 * 1024**3:
        errors.append("system_memory_is_below_64gib")
    if shared_memory_bytes < 16 * 1024**3:
        errors.append("shared_memory_is_below_16gib")
    # Zero model calls. This is a deployment gate: if either speculative guard
    # cannot be demonstrated here, the fingerprint fails and the contract that
    # pins this fingerprint cannot be built.
    speculative_guard = speculative_guard_probe()
    errors.extend(speculative_guard["errors"])
    model_files = model_file_manifest(model_path)
    document: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.runtime_fingerprint.v1",
        "decision": "PASS" if not errors else "FAIL",
        "errors": errors,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "system_memory_bytes": system_memory_bytes,
            "shared_memory_bytes": shared_memory_bytes,
            "model_filesystem_free_bytes": model_filesystem.free,
            "model_filesystem_is_gated": False,
            "task_root": str(task_root),
            "task_filesystem_free_bytes": task_filesystem.free,
        },
        "gpu": {
            "inventory": gpus,
            "topology": topology_probe["output"],
            "topology_probe": topology_probe,
        },
        "required_launch_environment": {
            "NCCL_CUMEM_HOST_ENABLE": "0",
        },
        "software": {
            "torch": metadata.version("torch"),
            "torch_cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "vllm": metadata.version("vllm"),
            "vllm_module": str(Path(vllm.__file__).resolve()),
            "xgrammar": metadata.version("xgrammar"),
            "xgrammar_module": str(Path(xgrammar.__file__).resolve()),
            # Pin the toolchain and the packages that decide tokenisation and
            # grammar compilation, so a rebuilt environment that differs in
            # any of them is visibly a different runtime.
            "uv": command_output(["uv", "--version"]),
            "distributions": {
                name: version
                for name, version in (
                    (name, _installed_version(name))
                    for name in sorted(TRACKED_DISTRIBUTIONS)
                )
                if version is not None
            },
        },
        "model": {
            "path": str(model_path),
            "file_count": len(model_files),
            "total_bytes": sum(item["size"] for item in model_files),
            "files": model_files,
            "tree_content_sha256": canonical_sha256(model_files),
        },
        "overlay_manifest_file_sha256": sha256_file(overlay_manifest_path),
        "speculative_guard": speculative_guard["checks"],
    }
    document["content_sha256"] = canonical_sha256(document)
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument(
        "--task-root",
        type=Path,
        required=True,
        help="filesystem the experiment writes to; this is the one gated on "
        "free space, not the model mount",
    )
    parser.add_argument("--overlay-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = build_fingerprint(
        model_path=args.model_path,
        task_root=args.task_root,
        overlay_manifest_path=args.overlay_manifest,
    )
    atomic_write_json(args.output.resolve(), document)
    print(
        json.dumps(
            {
                "decision": document["decision"],
                "content_sha256": document["content_sha256"],
                "model_tree_content_sha256": document["model"][
                    "tree_content_sha256"
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if document["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
