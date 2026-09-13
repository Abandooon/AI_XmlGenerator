#!/usr/bin/env python3
"""Draw Figure 8 from the preserved railway summary (Python + Matplotlib).

Run from any directory. The input defaults to the retained figure data.
New figures are written outside the evidence release. See docs/COMMANDS.md.

The input summary contains the original source hashes. This script reads its
counts directly; it neither reads nor modifies experimental results.
"""
from __future__ import annotations

import tempfile
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.transforms import Bbox


HERE = Path(__file__).resolve().parent


def read_data(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data["natural_arms"] != ["G0", "GS", "GF"]:
        raise ValueError("Unexpected generation/repair arm order")
    if data["controlled_arms"] != ["S", "V", "F"]:
        raise ValueError("Unexpected controlled-damage arm order")
    for key, denominator_key in (
        ("historical_G_counts", "historical_G_denominator"),
        ("controlled_R_counts", "controlled_R_denominator"),
        ("same_task_Luna_counts", "supplement_denominator"),
        ("Terra_counts", "supplement_denominator"),
    ):
        denominator = data[denominator_key]
        if type(denominator) is not int or denominator <= 0:
            raise ValueError(f"Invalid denominator: {denominator_key}")
        counts = data[key]
        if len(counts) != 3 or any(
            type(value) is not int or not 0 <= value <= denominator
            for value in counts
        ):
            raise ValueError(f"Invalid count series: {key}")
    if data.get("supplement_all_72_known") is not True:
        raise ValueError("The model-comparison data must be complete")
    return data



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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path,
        default=HERE.parent / "data" / "Fig8_railway_results_data.json",
    )
    parser.add_argument("--output-dir", type=Path, default=None, help='External directory; defaults to a new system temporary directory')
    args = parser.parse_args()
    args.output_dir = external_output(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="paper_figures_"))
    source = args.data.resolve()
    data = read_data(source)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, axes = plt.subplots(
        1, 3, figsize=(6.85, 2.85),
        gridspec_kw={"width_ratios": [1, 1, 1.45]},
    )
    fig.subplots_adjust(left=0.084, right=0.99, bottom=0.20, top=0.775, wspace=0.38)
    title_artists = []
    count_artists = []
    plotted = []
    titles = [
        ("(a) Generation and repair", "Luna - 3 runs per task"),
        ("(b) Repair of injected faults", "Luna - 3 runs per input"),
        ("(c) LLM comparison", "24 tasks - 1 run per model"),
    ]
    for ax, (title, subtitle) in zip(axes, titles):
        ax.set_ylim(0, 114)
        ax.set_yticks([0, 50, 100])
        ax.yaxis.grid(True, color="0.88", linewidth=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=7.4, length=2, pad=3)
        ax.spines["bottom"].set_color("0.4")
        ax.spines["left"].set_color("0.4")
        title_artists.extend([
            ax.text(0.5, 1.16, title, transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=8.3, fontweight="bold"),
            ax.text(0.5, 1.055, subtitle, transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=7.1, color="0.25"),
        ])
    axes[0].set_ylabel("Strict success rate (%)", fontsize=8, labelpad=6)

    def bars(ax, positions, counts, denominator, *, color, width, group, legend=None):
        values = [100 * value / denominator for value in counts]
        artists = ax.bar(positions, values, width=width, color=color,
                         edgecolor="0.1", linewidth=0.5, label=legend)
        for x, value, count, artist in zip(positions, values, counts, artists):
            label = f"{count}/{denominator}"
            count_artists.append(ax.text(
                x, value + 2.7, label, ha="center", va="bottom", fontsize=6.7,
            ))
            if abs(artist.get_height() - 100 * count / denominator) > 1e-12:
                raise RuntimeError("A bar height differs from its source count")
            plotted.append({"series": group, "count": count,
                            "denominator": denominator, "percentage": value,
                            "label": label})

    for ax, count_key, denominator_key, arm_key, group in (
        (axes[0], "historical_G_counts", "historical_G_denominator", "natural_arms", "G"),
        (axes[1], "controlled_R_counts", "controlled_R_denominator", "controlled_arms", "R"),
    ):
        bars(ax, [0, 1, 2], data[count_key], data[denominator_key],
             color="0.35", width=0.56, group=group)
        ax.set_xticks([0, 1, 2], data[arm_key])
        ax.set_xlim(-0.55, 2.55)

    ax = axes[2]
    for offset, key, color, model in (
        (-0.23, "same_task_Luna_counts", "0.76", "Luna"),
        (0.23, "Terra_counts", "0.25", "Terra"),
    ):
        bars(ax, [i + offset for i in range(3)], data[key], data["supplement_denominator"],
             color=color, width=0.38, group=model, legend=model)
    ax.set_xticks([0, 1, 2], data["natural_arms"])
    ax.set_xlim(-0.62, 2.62)
    legend = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16),
                       ncol=2, frameon=False, fontsize=7.3, handlelength=1.1,
                       handletextpad=0.4, columnspacing=1.2, borderaxespad=0)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = Bbox.from_bounds(0, 0, *fig.canvas.get_width_height())
    relevant = title_artists + count_artists + [legend, axes[0].yaxis.label]
    for artist in relevant:
        extent = artist.get_window_extent(renderer)
        if (extent.x0 < canvas.x0 or extent.y0 < canvas.y0 or
                extent.x1 > canvas.x1 or extent.y1 > canvas.y1):
            raise RuntimeError(f"Figure text extends outside the page: {artist}")
    for index, first in enumerate(count_artists):
        for second in count_artists[index + 1:]:
            if first.get_window_extent(renderer).overlaps(second.get_window_extent(renderer)):
                raise RuntimeError("Two bar-value labels overlap")
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise RuntimeError("Source data changed during plotting")

    outputs = {}
    for extension in ("svg", "pdf", "png"):
        output = args.output_dir / f"Fig8_railway_results.{extension}"
        fig.savefig(output, dpi=300, facecolor="white")
        outputs[output.name] = hashlib.sha256(output.read_bytes()).hexdigest()
    plt.close(fig)
    report = {
        "status": "PASS", "matplotlib_version": matplotlib.__version__,
        "source_data_name": source.name, "source_data_sha256": before,
        "source_data_unchanged": True, "count_series_read_from_input": True,
        "statistics_reestimated": False, "bar_count": len(plotted),
        "figure_inches": [6.85, 2.85], "font_family": "DejaVu Sans",
        "source_hashes": {key: value for key, value in data.items() if key.endswith("_sha256")},
        "plotted_values": plotted, "outputs_sha256": outputs,
        "count_labels_nonoverlapping": True, "key_text_within_page": True,
    }
    (args.output_dir / "Fig8_render_check.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
