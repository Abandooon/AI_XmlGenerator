"""Continuously record host and GPU metrics beside a U/G/A schedule run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def cpu_times() -> tuple[int, int]:
    fields = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()
    if not fields or fields[0] != "cpu" or len(fields) < 6:
        raise RuntimeError("unexpected_proc_stat_format")
    values = [int(value) for value in fields[1:]]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle


def memory_sample() -> dict[str, int]:
    fields = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        name, raw = line.split(":", 1)
        fields[name] = int(raw.strip().split()[0]) * 1024
    total = fields["MemTotal"]
    available = fields["MemAvailable"]
    return {
        "total_bytes": total,
        "available_bytes": available,
        "used_bytes": total - available,
    }


def gpu_sample() -> list[dict[str, int]]:
    output = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,utilization.gpu,memory.used,power.draw",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    records = []
    for line in output.splitlines():
        fields = [field.strip() for field in line.split(",")]
        records.append(
            {
                "index": int(fields[0]),
                "utilization_percent": int(fields[1]),
                "memory_used_mib": int(fields[2]),
                "power_draw_mw": int(round(float(fields[3]) * 1000)),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, default=0.25)
    args = parser.parse_args()
    output = args.output.resolve()
    stop_file = args.stop_file.resolve()
    if output.exists():
        raise FileExistsError(f"metrics output already exists: {output}")
    if stop_file.exists():
        raise FileExistsError(f"metrics stop file already exists: {stop_file}")
    if args.interval_seconds <= 0:
        raise ValueError("interval_seconds_must_be_positive")
    sequence = 0
    previous_total, previous_idle = cpu_times()
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        while not stop_file.exists():
            started_ns = time.time_ns()
            current_total, current_idle = cpu_times()
            total_delta = current_total - previous_total
            idle_delta = current_idle - previous_idle
            cpu_utilization = (
                100.0 * (total_delta - idle_delta) / total_delta
                if total_delta > 0
                else None
            )
            previous_total, previous_idle = current_total, current_idle
            record = {
                "schema_version": "atlas.vllm.uga.host_metrics.v1",
                "sequence": sequence,
                "timestamp_ns": started_ns,
                "load_average": os.getloadavg(),
                "cpu_utilization_percent": cpu_utilization,
                "memory": memory_sample(),
                "gpu": gpu_sample(),
            }
            stream.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            stream.flush()
            sequence += 1
            elapsed = (time.time_ns() - started_ns) / 1_000_000_000
            time.sleep(max(0.0, args.interval_seconds - elapsed))
        os.fsync(stream.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
