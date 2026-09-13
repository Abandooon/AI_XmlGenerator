"""Reassemble the unchanged Terra archive and run its offline review with caller Python/Java 8."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shutil, stat, subprocess, sys, zipfile

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def resolve_part(root, relative):
    name = PurePosixPath(relative)
    require(not name.is_absolute() and ".." not in name.parts and "\\" not in relative
            and ":" not in relative and name.parts[:1] == ("archives",), "Unsafe part path")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "Part escapes release directory")
    return path

def reassemble(root, manifest, target):
    require(not target.exists(), "Refusing to overwrite reconstructed ZIP")
    archive = manifest["archive"]
    offset, seen = 0, set()
    with target.open("xb") as output:
        for number, record in enumerate(manifest["parts"], 1):
            require(record["index"] == number and record["offset"] == offset
                    and record["path"] not in seen, "Part order, offset or identity differs")
            part = resolve_part(root, record["path"])
            require(part.is_file() and part.stat().st_size == record["bytes"], "Part absent or wrong size")
            hasher = hashlib.sha256()
            with part.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(block)
                    output.write(block)
            require(hasher.hexdigest() == record["sha256"], "Part SHA-256 differs")
            seen.add(record["path"])
            offset += record["bytes"]
    require(offset == archive["bytes"] and sha(target) == archive["sha256"], "Reassembled archive differs")
    return {"parts": len(seen), "bytes": offset, "sha256": archive["sha256"], "unchanged_original_zip": True}

def extract_checked(archive, destination, expected_count):
    require(not destination.exists(), "Extraction directory must be new")
    seen = set()
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        require(len(infos) == expected_count, "Archive member count differs")
        for member in infos:
            name, p = member.filename, PurePosixPath(member.filename)
            require(not p.is_absolute() and ".." not in p.parts and "\\" not in name and ":" not in name,
                    "Unsafe ZIP member")
            require(p.parts[:1] == ("ATLAS_TERRA_SUPPLEMENT",) and not member.is_dir(), "Unexpected archive root/member")
            require(not stat.S_ISLNK(member.external_attr >> 16) and not member.flag_bits & 1, "Link/encrypted member rejected")
            require(name.casefold() not in seen, "Duplicate/case-colliding ZIP member")
            seen.add(name.casefold())
        destination.mkdir()
        for member in infos:
            target = (destination / member.filename).resolve()
            require(target.is_relative_to(destination.resolve()), "ZIP member escapes extraction root")
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    return destination / "ATLAS_TERRA_SUPPLEMENT"

def run_logged(command, cwd, log_prefix, env):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=1800)
    log_prefix.with_suffix(".stdout.txt").write_text(result.stdout, encoding="utf-8")
    log_prefix.with_suffix(".stderr.txt").write_text(result.stderr, encoding="utf-8")
    require(result.returncode == 0, "Offline subprocess failed: " + log_prefix.name)
    return result.stdout


def external_output(path):
    """Keep newly generated files outside the evidence release."""
    path = Path(path).resolve()
    release = next((p for p in Path(__file__).resolve().parents
                    if (p / "verify_release.py").is_file()
                    and (p / "RELEASE_MANIFEST.json").is_file()),
                   Path(__file__).resolve().parent)
    if path == release or path.is_relative_to(release):
        raise ValueError("Output must be outside the evidence release")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path, help="New directory outside this release")
    parser.add_argument("--java", default="java", help="External Java 8 executable or PATH name")
    args = parser.parse_args()
    require(sys.version_info >= (3, 10), "Python 3.10+ required; Python 3.12 used in qualification")
    work = external_output(args.work_dir)
    require(not work.exists() and not work.is_relative_to(ROOT), "Work directory must be new and outside release")
    java = shutil.which(args.java)
    require(java is not None, "Java executable missing")
    java = str(Path(java).resolve())
    version = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=15)
    java_version = (version.stderr or version.stdout).strip()
    require(version.returncode == 0 and "1.8." in java_version, "Java 8 is required")
    manifest = read(ROOT / "PARTS_MANIFEST.json")
    work.mkdir(parents=True)
    output = work / "results"
    output.mkdir()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)
    try:
        archive = work / "terra_complete_original.zip"
        archive_check = reassemble(ROOT, manifest, archive)
        package = extract_checked(archive, work / "payload", manifest["archive"]["entries"])
        stdout = run_logged([sys.executable, "-B", str(package / "continuation3/delivery/verify_package.py")],
                            package, output / "package_integrity", env)
        integrity = json.loads(stdout)
        require(integrity.get("pass") is True, "Original package integrity check failed")
        review = output / "independent"
        run_logged([sys.executable, "-B", str(package / "review/continuation3/verify_final.py"),
                    "--package-root", str(package), "--output", str(review), "--java", java],
                   package, output / "native_audit", env)
        audit = read(review / "terra_independent_audit.json")
        require(audit["evidence_integrity"] == "PASS" and audit["study_completion"] == "COMPLETE",
                "Evidence check did not pass or study is incomplete")
        report = {"status": "PASS", "archive": archive_check, "package_integrity": integrity,
                  "evidence_integrity": audit["evidence_integrity"], "study_completion": audit["study_completion"],
                  "independent_report": "independent/terra_independent_audit.json", "independent_report_sha256": sha(review / "terra_independent_audit.json"),
                  "python_executable": sys.executable, "python_version": sys.version.split()[0],
                  "java_executable": java, "java_version": java_version,
                  "bundled_windows_python_executed": False, "bundled_java_required": False,
                  "network_or_model_calls": 0, "scope": "Repackaging/replay only; original ZIP and scientific sources unchanged"}
    except Exception as error:
        report = {"status": "FAIL", "error": type(error).__name__ + ": " + str(error), "network_or_model_calls": 0}
    (output / "REVIEW_RESULT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
