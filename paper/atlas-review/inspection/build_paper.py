"""Compile the current manuscript into a new external directory using Tectonic."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper/current/english"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--offline", action="store_true", help="Use an already populated Tectonic cache")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT) or (out.exists() and any(out.iterdir())):
        parser.error("Use a new or empty directory outside the release")
    executable = shutil.which(args.tectonic)
    if not executable:
        parser.error("Tectonic executable not found")
    out.mkdir(parents=True, exist_ok=True)
    command = [executable, "--untrusted", "--keep-logs", "--keep-intermediates", "--outdir", str(out)]
    if args.offline:
        command.append("--only-cached")
    command.append("main.tex")
    result = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (out / "build.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out / "build.stderr.txt").write_text(result.stderr, encoding="utf-8")
    pdf = out / "main.pdf"
    passed = result.returncode == 0 and pdf.is_file() and pdf.read_bytes().startswith(b"%PDF-")
    report = {"status": "PASS" if passed else "FAIL", "compiler_exit_code": result.returncode,
              "source": "paper/current/english/main.tex", "compiler": "Tectonic",
              "sources_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(SOURCE.iterdir()) if p.suffix in {".tex", ".bib", ".cls", ".bst", ".pdf"} and p.name != "main.pdf"},
              "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.is_file() else None,
              "scope": "Compilation and PDF creation; layout is reviewed separately"}
    (out / "BUILD_RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
