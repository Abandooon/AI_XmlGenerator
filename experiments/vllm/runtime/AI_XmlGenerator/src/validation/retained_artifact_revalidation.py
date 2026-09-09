"""Independent revalidation of the retained multi-component ARXML artifacts.

This is not a reproduction of the original RQ2 experiment and must never be
presented as one.  The generation conditions of that experiment are gone: the
retained performance records name no model, version, temperature or seed, and
three of the six Complex systems have no artifacts at all.  What can still be
established is what the surviving files themselves say, measured under stated
rules, against a hash-pinned schema.

Three rules separate this from the historical checker, which reported a higher
resolution rate than the artifacts support:

* references resolve within one system, never across a whole complexity tier.
  A tier-wide symbol table lets one system's entity satisfy another system's
  dangling reference, which is not cross-file integrity but name collision;
* a reference must match a full instance path.  Falling back to the trailing
  SHORT-NAME accepts any entity that happens to end with the same word;
* where a reference declares ``DEST``, the target's element type must agree,
  and an ambiguous target is a failure rather than a resolution.

Shared platform type files are counted and reported separately: they are inputs
every system was given, not artifacts any system generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lxml import etree

SCHEMA_VERSION = "atlas.rq2.retained_artifact_revalidation.v1"
REFERENCE_SUFFIX = "-REF"
TREF_SUFFIX = "-TREF"


def _local_name(tag: object) -> str:
    text = str(tag or "")
    return text.rsplit("}", 1)[-1]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_ref(value: str | None) -> str:
    if not value:
        return ""
    parts = [part for part in str(value).strip().replace("\\", "/").split("/") if part]
    return "/" + "/".join(parts)


class SystemIndex:
    """Instance paths and element types for exactly one generated system."""

    def __init__(self, paths: Iterable[Path]) -> None:
        self.paths = list(paths)
        self.trees: list[tuple[Path, etree._ElementTree]] = []
        self.parent: dict[etree._Element, etree._Element] = {}
        self.by_path: dict[str, list[etree._Element]] = defaultdict(list)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
        for path in self.paths:
            tree = etree.parse(str(path), parser)
            self.trees.append((path, tree))
            root = tree.getroot()
            for element in root.iter():
                if not isinstance(element.tag, str):
                    continue
                for child in element:
                    if isinstance(child.tag, str):
                        self.parent[child] = element
        for _path, tree in self.trees:
            for element in tree.getroot().iter():
                if not isinstance(element.tag, str):
                    continue
                if self._short_name(element) is None:
                    continue
                self.by_path[self._instance_path(element)].append(element)

    @staticmethod
    def _short_name(element: etree._Element) -> str | None:
        for child in element:
            if _local_name(child.tag) == "SHORT-NAME" and child.text and child.text.strip():
                return child.text.strip()
        return None

    def _instance_path(self, element: etree._Element) -> str:
        names: list[str] = []
        current: etree._Element | None = element
        while current is not None:
            name = self._short_name(current)
            if name:
                names.append(name)
            current = self.parent.get(current)
        return _normalized_ref("/".join(reversed(names)))

    def resolve(self, reference: str, dest: str | None) -> tuple[str, str]:
        """Return ``(status, detail)`` for one reference.

        ``status`` is ``resolved``, ``unresolved`` or ``ambiguous``.  There is no
        trailing-name fallback: a reference either names an instance path that
        exists in this system, or it does not.
        """
        target = _normalized_ref(reference)
        if not target:
            return "unresolved", "empty reference"
        candidates = self.by_path.get(target, [])
        if not candidates:
            return "unresolved", "no instance path matches"
        if len(candidates) > 1:
            return "ambiguous", f"{len(candidates)} entities share this instance path"
        if dest:
            actual = _local_name(candidates[0].tag)
            if actual.upper() != dest.strip().upper():
                return "unresolved", f"DEST {dest} does not match target type {actual}"
        return "resolved", ""


class IndependentIndex:
    """A second resolver written a different way, used only to cross-check.

    It walks ``getparent()`` instead of a precomputed parent map and reads
    SHORT-NAME through XPath instead of iterating children.  Agreement between
    two implementations that share no code path is what turns "the checker says
    1,781 references do not resolve" into a claim about the artifacts rather
    than about one function.
    """

    def __init__(self, paths: Iterable[Path]) -> None:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
        self.by_path: dict[str, list[str]] = defaultdict(list)
        for path in paths:
            root = etree.parse(str(path), parser).getroot()
            for element in root.iter():
                if not isinstance(element.tag, str):
                    continue
                names = element.xpath("*[local-name()='SHORT-NAME']")
                if not names or not (names[0].text or "").strip():
                    continue
                chain: list[str] = []
                current = element
                while current is not None:
                    own = current.xpath("*[local-name()='SHORT-NAME']")
                    if own and (own[0].text or "").strip():
                        chain.append((own[0].text or "").strip())
                    current = current.getparent()
                self.by_path[_normalized_ref("/".join(reversed(chain)))].append(
                    _local_name(element.tag)
                )

    def resolve(self, reference: str, dest: str | None) -> str:
        target = _normalized_ref(reference)
        if not target:
            return "unresolved"
        types = self.by_path.get(target, [])
        if not types:
            return "unresolved"
        if len(types) > 1:
            return "ambiguous"
        if dest and types[0].upper() != dest.strip().upper():
            return "unresolved"
        return "resolved"


def _references(tree: etree._ElementTree) -> list[tuple[etree._Element, str, str | None]]:
    found: list[tuple[etree._Element, str, str | None]] = []
    for element in tree.getroot().iter():
        if not isinstance(element.tag, str):
            continue
        name = _local_name(element.tag).upper()
        if not (name.endswith(REFERENCE_SUFFIX) or name.endswith(TREF_SUFFIX)):
            continue
        text = (element.text or "").strip()
        if not text:
            continue
        dest = element.get("DEST")
        found.append((element, text, dest))
    return found


def revalidate_system(
    system: str,
    paths: list[Path],
    xsd: etree.XMLSchema,
    shared: list[Path] | None = None,
) -> dict[str, Any]:
    # The shared platform type files were given to every system as input, so a
    # reference into them is legitimately resolvable.  They join the resolution
    # context and are never counted as this system's output.
    index = SystemIndex(list(paths) + list(shared or []))
    cross = IndependentIndex(list(paths) + list(shared or []))
    generated = {path.resolve() for path in paths}
    files: list[dict[str, Any]] = []
    totals = {
        "references": 0, "resolved": 0, "unresolved": 0, "ambiguous": 0,
        "cross_check_agreements": 0, "cross_check_disagreements": 0,
    }
    disagreements: list[dict[str, str]] = []
    xsd_pass = 0
    for path, tree in index.trees:
        if path.resolve() not in generated:
            continue
        valid = bool(xsd.validate(tree))
        xsd_pass += int(valid)
        record: dict[str, Any] = {
            "file": path.name,
            "sha256": _sha256_file(path),
            "xsd_valid": valid,
            "xsd_errors": [] if valid else [
                f"{entry.path}: {entry.message}" for entry in xsd.error_log
            ][:5],
            "references": 0,
            "resolved": 0,
            "unresolved": [],
            "ambiguous": [],
        }
        for _element, reference, dest in _references(tree):
            record["references"] += 1
            totals["references"] += 1
            status, detail = index.resolve(reference, dest)
            second = cross.resolve(reference, dest)
            if second == status:
                totals["cross_check_agreements"] += 1
            else:
                totals["cross_check_disagreements"] += 1
                disagreements.append({
                    "reference": reference, "primary": status, "independent": second,
                })
            if status == "resolved":
                record["resolved"] += 1
                totals["resolved"] += 1
            elif status == "ambiguous":
                record["ambiguous"].append({"reference": reference, "detail": detail})
                totals["ambiguous"] += 1
            else:
                record["unresolved"].append({
                    "reference": reference, "dest": dest, "detail": detail
                })
                totals["unresolved"] += 1
        files.append(record)
    return {
        "system": system,
        "file_count": len(paths),
        "xsd_pass_count": xsd_pass,
        "xsd_pass": xsd_pass == len(paths),
        **totals,
        "resolution_rate": (
            totals["resolved"] / totals["references"] if totals["references"] else None
        ),
        "cross_check_disagreement_samples": disagreements[:10],
        "files": sorted(files, key=lambda item: item["file"]),
    }


def _runtime() -> dict[str, str]:
    import platform
    from importlib import metadata

    versions: dict[str, str] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
    try:
        versions["lxml"] = metadata.version("lxml")
    except Exception:
        versions["lxml"] = "UNKNOWN"
    versions["libxml2"] = ".".join(str(part) for part in etree.LIBXML_VERSION)
    versions["libxslt"] = ".".join(str(part) for part in etree.LIBXSLT_VERSION)
    return versions


def _requirement_provenance(
    project_root: Path, tiers: tuple[str, ...], observed: dict[str, list[str]]
) -> dict[str, Any]:
    """Name the systems the requirements declare and those with no artifacts.

    Reporting a resolution rate over the surviving systems without naming the
    absent ones would present a partial corpus as the whole one.
    """
    declared: dict[str, list[str]] = {}
    files: dict[str, str] = {}
    for tier in tiers:
        path = project_root / "nlp_require" / f"{tier}.json"
        if not path.is_file():
            raise FileNotFoundError(f"requirement file not found: {path}")
        files[_relative(path, project_root)] = _sha256_file(path)
        records = json.loads(path.read_text(encoding="utf-8"))
        declared[tier] = [
            str(item.get("system_name") or item.get("name") or item.get("id") or "")
            for item in records
        ]
        if not all(declared[tier]):
            raise ValueError(f"{path} has a record without a system name")
    missing: dict[str, list[dict[str, Any]]] = {}
    for tier in tiers:
        names = declared[tier]
        present = set(observed.get(tier) or [])
        missing[tier] = [
            {"ordinal": index + 1, "system": f"{tier}_{index + 1:02d}", "name": name}
            for index, name in enumerate(names)
            if f"{tier}_{index + 1:02d}" not in present
        ]
    return {
        "requirement_files": files,
        "declared_systems": declared,
        "declared_system_count": sum(len(v) for v in declared.values()),
        "systems_with_artifacts": {tier: sorted(observed.get(tier) or []) for tier in tiers},
        "systems_without_artifacts": missing,
        "missing_system_count": sum(len(v) for v in missing.values()),
    }


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.name


def revalidate(root: Path, xsd_path: Path, tiers: tuple[str, ...]) -> dict[str, Any]:
    xsd = etree.XMLSchema(etree.parse(str(xsd_path)))
    project_root = Path(__file__).resolve().parents[2]
    tier_reports: dict[str, Any] = {}
    shared_files: dict[str, list[dict[str, str]]] = {}
    observed_systems: dict[str, list[str]] = {}
    for tier in tiers:
        directory = root / tier
        if not directory.is_dir():
            raise FileNotFoundError(f"tier directory not found: {directory}")
        by_system: dict[str, list[Path]] = defaultdict(list)
        shared: list[Path] = []
        for path in sorted(directory.glob("*.arxml")):
            if path.name.startswith(f"{tier}_"):
                by_system["_".join(path.name.split("_")[:2])].append(path)
            else:
                shared.append(path)
        shared_files[tier] = [
            {"file": path.name, "sha256": _sha256_file(path)} for path in shared
        ]
        systems = [
            revalidate_system(system, paths, xsd, shared)
            for system, paths in sorted(by_system.items())
        ]
        aggregate = {
            key: sum(item[key] for item in systems)
            for key in ("file_count", "xsd_pass_count", "references", "resolved",
                        "unresolved", "ambiguous", "cross_check_agreements",
                        "cross_check_disagreements")
        }
        observed_systems.setdefault(tier, []).extend(sorted(by_system))
        tier_reports[tier] = {
            "system_count": len(systems),
            **aggregate,
            "resolution_rate": (
                aggregate["resolved"] / aggregate["references"]
                if aggregate["references"] else None
            ),
            "systems": systems,
        }
    grand = {
        key: sum(report[key] for report in tier_reports.values())
        for key in ("system_count", "file_count", "xsd_pass_count", "references",
                    "resolved", "unresolved", "ambiguous", "cross_check_agreements",
                    "cross_check_disagreements")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "is_reproduction_of_original_experiment": False,
        "note": (
            "Independent revalidation of retained artifacts. The original "
            "generation conditions are not recoverable: the retained records name "
            "no model, version, temperature or seed, and three Complex systems "
            "have no artifacts. These figures describe the surviving files only."
        ),
        "rules": {
            "reference_scope": "per_system",
            "path_matching": "full_instance_path_only",
            "trailing_short_name_fallback": False,
            "dest_type_checked": True,
            "ambiguous_target": "counted_as_unresolved_failure",
            "shared_type_files": (
                "part of every system's resolution context as supplied input; "
                "never counted as that system's output"
            ),
        },
        "inputs": {
            "artifact_root": _relative(root, project_root),
            "xsd_path": _relative(xsd_path, project_root),
            "xsd_sha256": _sha256_file(xsd_path),
            "source_file": _relative(Path(__file__), project_root),
            "source_sha256": _sha256_file(Path(__file__)),
        },
        "runtime": _runtime(),
        "requirement_provenance": _requirement_provenance(
            project_root, tiers, observed_systems
        ),
        "shared_type_files": {
            tier: [
                {"file": item["file"], "sha256": item["sha256"]} for item in entries
            ]
            for tier, entries in shared_files.items()
        },
        "tiers": tier_reports,
        "totals": {
            **grand,
            "resolution_rate": (
                grand["resolved"] / grand["references"] if grand["references"] else None
            ),
            "xsd_pass_rate": (
                grand["xsd_pass_count"] / grand["file_count"] if grand["file_count"] else None
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=project_root / "generated_arxml")
    parser.add_argument(
        "--xsd", type=Path, default=project_root / "src/validation/data/AUTOSAR_4-2-2.xsd"
    )
    parser.add_argument("--tiers", nargs="+", default=["simple", "middle", "complex"])
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "reports/rq2_retained_artifact_revalidation.json",
    )
    args = parser.parse_args(argv)

    manifest = revalidate(args.root, args.xsd, tuple(args.tiers))
    manifest["content_sha256"] = _canonical_sha256(
        {k: v for k, v in manifest.items() if k != "created_at_utc"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({
        "output": str(args.output),
        "content_sha256": manifest["content_sha256"],
        "totals": manifest["totals"],
        "tiers": {
            tier: {
                key: report[key]
                for key in ("system_count", "file_count", "xsd_pass_count",
                            "references", "resolved", "unresolved", "ambiguous",
                            "resolution_rate")
            }
            for tier, report in manifest["tiers"].items()
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
