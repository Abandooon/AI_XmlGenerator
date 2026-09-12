"""Render Figure 7 from retained decoding traces and structural outcomes.

Run without a model, GPU, API key or network connection. Repeated traces are
merged only after their positions and step counts have been checked for equality.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path,
                        default=here.parent / "data/Fig7_vllm_intervention_data.json")
    parser.add_argument("--output-dir", type=Path, default=here.parent / "output")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for row in data["audit_requests"]:
        grouped[row["case_id"]].append(row)
    order = sorted(grouped, key=lambda c: grouped[c][0]["formal_case_ordinal"])
    pairs = {row["case_id"]: row for row in data["case_pairs"]}
    assert len(order) == 20 and len(data["audit_requests"]) == 60
    assert set(pairs) == set(order)
    for case in order:
        rows = sorted(grouped[case], key=lambda row: row["repeat"])
        assert [row["repeat"] for row in rows] == [1, 2, 3]
        signatures = {
            (tuple(row["bound_sample_ordinals"]), row["total_steps"],
             row["evaluable_steps"], row["bound_steps"])
            for row in rows
        }
        assert len(signatures) == 1, f"Cannot merge nonidentical traces: {case}"
        for row in rows:
            assert row["bound_steps"] == len(row["bound_sample_ordinals"])
            assert all(0 <= s < row["total_steps"] for s in row["bound_sample_ordinals"])
        grouped[case] = rows
    bound = sum(row["bound_steps"] for row in data["audit_requests"])
    evaluable = sum(row["evaluable_steps"] for row in data["audit_requests"])
    assert bound == data["summary"]["bound_steps"] == 516
    assert evaluable == data["summary"]["evaluable_steps"] == 54942
    assert sum(pairs[c]["u_pass_count"] for c in order) == data["summary"]["u_pass_runs"]
    assert sum(pairs[c]["g_pass_count"] for c in order) == data["summary"]["g_pass_runs"]

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8,
        "axes.unicode_minus": False, "svg.fonttype": "none",
        "pdf.fonttype": 42, "axes.linewidth": .5,
        "xtick.major.width": .5, "svg.hashsalt": "figure7-retained-traces",
    })
    fig = plt.figure(figsize=(6.85, 4.25), facecolor="white")
    ax = fig.add_axes([.17, .125, .465, .755])
    bx = fig.add_axes([.745, .125, .245, .755])
    fig.text(.17, .957, "(a) Decoding interventions", fontsize=8.8, weight="bold")
    fig.text(.715, .957, "(b) Structural acceptance", fontsize=8.6, weight="bold")
    for j, case in enumerate(order):
        if j % 2 == 0:
            ax.axhspan(j - .5, j + .5, color=".955", zorder=0)
        row = grouped[case][0]
        ax.hlines(j, 0, 100, color=".86", linewidth=.3, zorder=1)
        progress = [(s + 1) / row["total_steps"] * 100
                    for s in row["bound_sample_ordinals"]]
        ax.plot(progress, [j] * len(progress), linestyle="None", marker="|",
                markersize=4.4, color=".12", markeredgewidth=.75, zorder=3)
        for col, key in enumerate(["u_pass_count", "g_pass_count"]):
            count = pairs[case][key]
            assert 0 <= count <= 3
            bx.add_patch(Rectangle((col - .42, j - .43), .84, .86,
                         facecolor=".25" if count == 3 else "white",
                         edgecolor=".45", linewidth=.5))
            bx.text(col, j, f"{count}/3", ha="center", va="center",
                    color="white" if count == 3 else ".1", fontsize=8)
    ax.set_xlim(-1, 101)
    ax.set_ylim(19.5, -.5)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_yticks(range(20), order, fontsize=7.4)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlabel("Decoding progress (% of output steps)", fontsize=7.5, labelpad=6)
    for name in ["top", "right", "left"]:
        ax.spines[name].set_visible(False)
    bx.set_xlim(-.58, 1.58)
    bx.set_ylim(19.5, -.5)
    bx.set_xticks([0, 1], ["U: Prompt\nonly", "G: Constrained\ndecoding"])
    bx.xaxis.tick_top()
    bx.tick_params(axis="x", length=0, pad=4, labelsize=7.2)
    bx.set_yticks([])
    for spine in bx.spines.values():
        spine.set_visible(False)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "svg", "pdf"]:
        metadata = {"Date": None} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None} if ext == "pdf" else None)
        fig.savefig(args.output_dir / f"Fig7_vllm_intervention.{ext}",
                    dpi=300, facecolor="white", metadata=metadata)
    plt.close(fig)
    receipt = {
        "figure": 7, "source_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "cases": len(order), "requests": len(data["audit_requests"]),
        "identical_repeats_merged_per_case": 3,
        "bound_steps": bound, "evaluable_steps": evaluable,
        "u_pass_runs": sum(pairs[c]["u_pass_count"] for c in order),
        "g_pass_runs": sum(pairs[c]["g_pass_count"] for c in order),
        "coordinate": "100 * (zero_based_sample_ordinal + 1) / total_steps",
        "bottom_summary_annotations": False,
        "matplotlib_version": matplotlib.__version__,
    }
    (args.output_dir / "Fig7_plot_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
