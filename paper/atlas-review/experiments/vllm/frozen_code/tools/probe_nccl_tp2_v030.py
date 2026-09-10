"""Two-rank NCCL gate for the frozen ATLAS tensor-parallel launch policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any


RECORD_PREFIX = "ATLAS_NCCL_PROBE_RECORD="
REQUIRED_NCCL_CUMEM_HOST_ENABLE = "0"


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def run_worker() -> int:
    import torch
    import torch.distributed as dist

    started = time.monotonic()
    if os.environ.get("NCCL_CUMEM_HOST_ENABLE") != (
        REQUIRED_NCCL_CUMEM_HOST_ENABLE
    ):
        raise RuntimeError("nccl_cumem_host_enable_policy_missing")
    dist.init_process_group(backend="nccl")
    try:
        rank = dist.get_rank()
        world_size = dist.get_world_size()
        local_rank = int(os.environ["LOCAL_RANK"])
        if world_size != 2:
            raise RuntimeError(f"unexpected_world_size:{world_size}")
        torch.cuda.set_device(local_rank)
        data = torch.ones(128, dtype=torch.float32, device=f"cuda:{local_rank}")
        dist.all_reduce(data, op=dist.ReduceOp.SUM)
        torch.cuda.synchronize(local_rank)
        value = data.mean().item()
        if value != float(world_size):
            raise RuntimeError(f"all_reduce_value_mismatch:{value}:{world_size}")
        record = {
            "decision": "PASS",
            "hostname": socket.gethostname(),
            "rank": rank,
            "world_size": world_size,
            "local_rank": local_rank,
            "mean": value,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "nccl_version": list(torch.cuda.nccl.version()),
            "nccl_cumem_host_enable": os.environ.get(
                "NCCL_CUMEM_HOST_ENABLE"
            ),
            "nccl_p2p_disable": os.environ.get("NCCL_P2P_DISABLE"),
        }
        record_root = os.environ.get("ATLAS_NCCL_PROBE_RECORD_ROOT")
        if not record_root:
            raise RuntimeError("nccl_probe_record_root_missing")
        atomic_write_json(Path(record_root) / f"rank-{rank}.json", record)
        print(f"{RECORD_PREFIX}rank-{rank}.json", flush=True)
    finally:
        dist.destroy_process_group()
    return 0


def run_parent(output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = "0,1"
    environment["NCCL_CUMEM_HOST_ENABLE"] = REQUIRED_NCCL_CUMEM_HOST_ENABLE
    environment.pop("NCCL_P2P_DISABLE", None)
    command = [
        sys.executable,
        "-m",
        "torch.distributed.run",
        "--standalone",
        "--nproc-per-node=2",
        str(Path(__file__).resolve()),
        "--worker",
    ]
    started = time.monotonic()
    with tempfile.TemporaryDirectory(
        prefix="atlas-nccl-ranks-",
        dir=output_path.parent,
    ) as temporary:
        record_root = Path(temporary)
        environment["ATLAS_NCCL_PROBE_RECORD_ROOT"] = str(record_root)
        completed = subprocess.run(
            command,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
            check=False,
        )
        records = []
        for rank in (0, 1):
            record_path = record_root / f"rank-{rank}.json"
            if record_path.is_file():
                value = json.loads(record_path.read_text(encoding="utf-8"))
                if not isinstance(value, dict):
                    raise RuntimeError(f"rank_record_not_object:{rank}")
                records.append(value)
    errors: list[str] = []
    if completed.returncode != 0:
        errors.append(f"torchrun_exit:{completed.returncode}")
    if sorted(item.get("rank") for item in records) != [0, 1]:
        errors.append("rank_inventory_mismatch")
    for record in records:
        if record.get("decision") != "PASS":
            errors.append(f"rank_{record.get('rank')}:not_pass")
        if record.get("world_size") != 2 or record.get("mean") != 2.0:
            errors.append(f"rank_{record.get('rank')}:all_reduce_mismatch")
        if record.get("nccl_cumem_host_enable") != (
            REQUIRED_NCCL_CUMEM_HOST_ENABLE
        ):
            errors.append(f"rank_{record.get('rank')}:cumem_policy_mismatch")
        if record.get("nccl_p2p_disable") is not None:
            errors.append(f"rank_{record.get('rank')}:unexpected_p2p_override")
    document: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.nccl_tp2_regression.v1",
        "decision": "PASS" if not errors else "FAIL",
        "model_request_count": 0,
        "world_size": 2,
        "required_launch_environment": {
            "NCCL_CUMEM_HOST_ENABLE": REQUIRED_NCCL_CUMEM_HOST_ENABLE,
        },
        "p2p_override_used": False,
        "records": sorted(records, key=lambda item: int(item.get("rank", -1))),
        "subprocess_output_sha256": hashlib.sha256(
            completed.stdout.encode("utf-8")
        ).hexdigest(),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "errors": errors,
    }
    if errors:
        document["subprocess_output_tail"] = completed.stdout[-4096:]
    document["content_sha256"] = canonical_sha256(document)
    atomic_write_json(output_path, document)
    print(
        json.dumps(
            {
                "decision": document["decision"],
                "model_request_count": 0,
                "rank_count": len(records),
                "content_sha256": document["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        return run_worker()
    if args.output is None:
        parser.error("--output is required outside --worker mode")
    return run_parent(args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
