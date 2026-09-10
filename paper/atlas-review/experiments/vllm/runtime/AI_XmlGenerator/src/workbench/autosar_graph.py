"""Small dependency-free AUTOSAR component/port/interface graph renderer."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _direct_text(element: ET.Element, name: str) -> str:
    for child in list(element):
        if _tag(child) == name:
            return str(child.text or "").strip()
    return ""


def _ref_name(text: str) -> str:
    return str(text or "").strip().rstrip("/").rsplit("/", 1)[-1]


def _iter_input_paths(paths: Iterable[str | Path]) -> list[Path]:
    result: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in {".arxml", ".xml"}:
            result.append(path)
    if not result:
        raise ValueError("select at least one existing ARXML/XML file")
    return sorted(set(result))


def build_autosar_graph(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Extract component, runnable, port, interface, and data-element relations."""

    files = _iter_input_paths(paths)
    nodes: dict[str, dict[str, str]] = {}
    edges: set[tuple[str, str, str]] = set()

    def node(kind: str, name: str, detail: str = "") -> str:
        clean = name or f"unnamed-{len(nodes) + 1}"
        identifier = f"{kind}:{clean}"
        nodes.setdefault(
            identifier,
            {"id": identifier, "kind": kind, "label": clean, "detail": detail},
        )
        return identifier

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as error:
            raise ValueError(f"cannot parse {path.name}: {error}") from error

        for element in root.iter():
            kind = _tag(element)
            if kind == "APPLICATION-SW-COMPONENT-TYPE":
                component_name = _direct_text(element, "SHORT-NAME")
                component_id = node("component", component_name, path.name)
                for descendant in element.iter():
                    descendant_kind = _tag(descendant)
                    if descendant_kind in {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"}:
                        port_name = _direct_text(descendant, "SHORT-NAME")
                        port_kind = "p_port" if descendant_kind.startswith("P-") else "r_port"
                        port_id = node(port_kind, port_name, descendant_kind)
                        edges.add((component_id, port_id, "contains"))
                        for ref in descendant.iter():
                            if _tag(ref) in {
                                "PROVIDED-INTERFACE-TREF",
                                "REQUIRED-INTERFACE-TREF",
                            }:
                                interface_name = _ref_name(ref.text or "")
                                interface_id = node("interface", interface_name)
                                edges.add((port_id, interface_id, "typed by"))
                    elif descendant_kind == "RUNNABLE-ENTITY":
                        runnable_name = _direct_text(descendant, "SHORT-NAME")
                        runnable_id = node("runnable", runnable_name)
                        edges.add((component_id, runnable_id, "executes"))
                        for ref in descendant.iter():
                            if _tag(ref) == "PORT-PROTOTYPE-REF":
                                port_name = _ref_name(ref.text or "")
                                destination = str(ref.attrib.get("DEST") or "")
                                port_kind = "p_port" if destination == "P-PORT-PROTOTYPE" else "r_port"
                                port_id = node(port_kind, port_name, destination)
                                edges.add((runnable_id, port_id, "accesses"))

            elif kind == "SENDER-RECEIVER-INTERFACE":
                interface_name = _direct_text(element, "SHORT-NAME")
                interface_id = node("interface", interface_name, path.name)
                for descendant in element.iter():
                    if _tag(descendant) == "VARIABLE-DATA-PROTOTYPE":
                        data_name = _direct_text(descendant, "SHORT-NAME")
                        data_id = node("data", data_name)
                        edges.add((interface_id, data_id, "carries"))

    ordered_nodes = sorted(nodes.values(), key=lambda item: (item["kind"], item["label"]))
    return {
        "files": [str(path) for path in files],
        "nodes": ordered_nodes,
        "edges": [
            {"source": source, "target": target, "label": label}
            for source, target, label in sorted(edges)
        ],
        "counts": {
            kind: sum(item["kind"] == kind for item in ordered_nodes)
            for kind in ("component", "runnable", "p_port", "r_port", "interface", "data")
        },
    }


def render_autosar_svg(graph: dict[str, Any]) -> str:
    """Render a Simulink-like, read-only SVG without browser dependencies."""

    nodes = list(graph.get("nodes") or [])
    if not nodes:
        return "<div class='atlas-empty'>No AUTOSAR entities were found.</div>"
    columns = {
        "component": 40,
        "runnable": 310,
        "p_port": 310,
        "r_port": 310,
        "interface": 650,
        "data": 960,
    }
    colors = {
        "component": ("#dbeafe", "#2563eb"),
        "runnable": ("#e5e7eb", "#4b5563"),
        "p_port": ("#dcfce7", "#16a34a"),
        "r_port": ("#f3e8ff", "#9333ea"),
        "interface": ("#ffedd5", "#ea580c"),
        "data": ("#fef9c3", "#ca8a04"),
    }
    by_kind: dict[str, list[dict[str, str]]] = {}
    for item in nodes:
        by_kind.setdefault(item["kind"], []).append(item)
    positions: dict[str, tuple[int, int]] = {}
    for kind, items in by_kind.items():
        x = columns.get(kind, 650)
        for index, item in enumerate(items):
            positions[item["id"]] = (x, 55 + index * 88)
    height = max(y for _, y in positions.values()) + 100

    parts = [
        "<div class='atlas-graph-shell'>",
        f"<svg viewBox='0 0 1240 {height}' role='img' aria-label='AUTOSAR component graph'>",
        "<defs><marker id='atlas-arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'><path d='M 0 0 L 10 5 L 0 10 z' fill='#64748b'/></marker></defs>",
    ]
    for edge in graph.get("edges") or []:
        if edge["source"] not in positions or edge["target"] not in positions:
            continue
        sx, sy = positions[edge["source"]]
        tx, ty = positions[edge["target"]]
        parts.append(
            f"<path d='M {sx + 220} {sy + 28} C {sx + 250} {sy + 28}, {tx - 30} {ty + 28}, {tx} {ty + 28}' stroke='#64748b' stroke-width='1.5' fill='none' marker-end='url(#atlas-arrow)'/>"
        )
        label_x = (sx + tx + 220) / 2
        label_y = (sy + ty) / 2 + 20
        parts.append(
            f"<text x='{label_x:.0f}' y='{label_y:.0f}' text-anchor='middle' font-size='11' fill='#475569'>{html.escape(str(edge['label']))}</text>"
        )
    for item in nodes:
        x, y = positions[item["id"]]
        fill, stroke = colors.get(item["kind"], ("#f8fafc", "#64748b"))
        label = html.escape(item["label"][:32])
        kind = html.escape(item["kind"].replace("_", " ").upper())
        detail = html.escape(str(item.get("detail") or "")[:38])
        parts.extend(
            [
                f"<g><rect x='{x}' y='{y}' width='220' height='58' rx='8' fill='{fill}' stroke='{stroke}' stroke-width='2'/>",
                f"<text x='{x + 12}' y='{y + 20}' font-size='10' font-weight='700' fill='{stroke}'>{kind}</text>",
                f"<text x='{x + 12}' y='{y + 39}' font-size='13' font-weight='600' fill='#0f172a'>{label}</text>",
                f"<title>{label} {detail}</title></g>",
            ]
        )
    parts.extend(["</svg>", "</div>"])
    return "".join(parts)
