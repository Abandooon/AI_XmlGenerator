"""Browser-level workbench condition-isolation gate; no provider is constructed."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = Path(r"E:\git projects\AI_XmlGenerator")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _runtime_paths() -> tuple[Path, Path, Path]:
    cache = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    )
    node = Path(os.environ.get("ATLAS_NODE") or cache / "bin/node.exe")
    modules = Path(os.environ.get("ATLAS_NODE_MODULES") or cache / "node_modules")
    browser_candidates = (
        Path(os.environ["ATLAS_BROWSER"])
        if os.environ.get("ATLAS_BROWSER")
        else None,
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    )
    browser = next((item for item in browser_candidates if item and item.is_file()), None)
    if not node.is_file() or not modules.is_dir() or browser is None:
        raise RuntimeError("workbench browser gate requires bundled Node/Playwright and Edge")
    return node, modules, browser


def _wait_ready(base_url: str, server: subprocess.Popen[str]) -> None:
    for _ in range(120):
        if server.poll() is not None:
            output = server.stdout.read() if server.stdout else ""
            raise RuntimeError("workbench server exited before readiness: " + output[-2000:])
        try:
            with urllib.request.urlopen(base_url, timeout=0.25) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("workbench server did not become ready")


def _events(study_root: Path, participant: str, condition: str) -> list[dict]:
    path = study_root / participant / f"T1.{condition}.events.jsonl"
    if not path.is_file():
        raise RuntimeError(f"browser session did not create {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> int:
    node, modules, browser = _runtime_paths()
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="atlas-gradio-browser-") as raw:
        temporary = Path(raw)
        study_root = temporary / "study"
        assignment = temporary / "condition_assignments.json"
        assignment.write_text(
            json.dumps(
                {
                    "schema_version": "atlas.workbench.assignment.v1",
                    "assignments": [
                        {"participant": "P01", "task": "T1", "condition": "manual"},
                        {
                            "participant": "P02",
                            "task": "T1",
                            "condition": "atlas_assisted",
                        },
                    ],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        environment = dict(os.environ)
        environment.update(
            {
                "ATLAS_WORKBENCH_ASSIGNMENT_TABLE": str(assignment),
                "ATLAS_WORKBENCH_STUDY_ROOT": str(study_root),
                "LLM_API_KEY": "offline-browser-placeholder",
            }
        )
        launch = (
            "import atlas_workbench as a; "
            f"a.demo.queue().launch(server_name='127.0.0.1', server_port={port}, "
            "share=False, show_error=True)"
        )
        server = subprocess.Popen(
            [sys.executable, "-B", "-c", launch],
            cwd=REPOSITORY,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            _wait_ready(base_url, server)
            node_environment = dict(environment)
            node_environment["NODE_PATH"] = str(modules)
            result = subprocess.run(
                [
                    str(node),
                    str(ROOT / "verify_workbench_browser.cjs"),
                    base_url,
                    str(browser),
                ],
                cwd=ROOT,
                env=node_environment,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            if result.returncode:
                raise RuntimeError("browser assertions failed: " + result.stderr[-3000:])
            browser_result = json.loads(result.stdout.splitlines()[-1])
            manual_events = _events(study_root, "P01", "manual")
            assisted_events = _events(study_root, "P02", "atlas_assisted")
            for records in (manual_events, assisted_events):
                if [item.get("event") for item in records] != ["START"]:
                    raise RuntimeError("opening a browser session did not emit exactly START")
                payload = records[0].get("payload") or {}
                if not payload.get("allocation_sha256") or not payload.get(
                    "assignment_table_sha256"
                ):
                    raise RuntimeError("START does not pin allocation provenance")
            print(
                json.dumps(
                    {
                        "decision": "PASS",
                        "browser": browser_result,
                        "manual_events": 1,
                        "assisted_events": 1,
                        "external_model_api_calls": 0,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        finally:
            server.terminate()
            try:
                server.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
