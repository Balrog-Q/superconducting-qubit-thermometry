"""Compare per-experiment running times of the new workflow-based measurement
script against the old (hand-rolled) measurement script.

Timing is recovered from the LabOne Q log messages that are stored in the
notebook outputs.  Two quantities are available:

* wall time  -- ``Finished near-time execution`` timestamp minus the
  ``Starting near-time execution`` timestamp.  This is the real time the
  measurement took on the instruments.
* RT estimate -- ``Estimated RT execution time: X s`` from the compiler
  report.  This is the duration of the real-time pulse sequence only.

The wall time is preferred.  Runs that were executed against the emulator
(``Untitled.ipynb``) finish in milliseconds, so for those the compiler's RT
estimate is used instead -- it is the physically meaningful duration and is
within a few percent of the hardware wall time (verified on the cells of
``ES-008-BC_2-1_8853_CD1.ipynb`` that do have hardware data).

Experiments are located by their markdown section heading rather than by cell
index, so the script keeps working when cells are added or removed.  Within a
section the *first* near-time execution is used, which is the primary
measurement (later cells in a section are chevrons, repeats or sweeps).

Every value can be overridden by hand in the ``MANUAL_TIMES`` table below, for
example to enter a time that was taken from a lab notebook, or to correct an
experiment whose outputs were cleared.  Manual values win over anything that is
found in the notebooks; use ``--ignore-manual`` to see the scraped values only.

Usage
-----
    python plot_experiment_runtimes.py
    python plot_experiment_runtimes.py --log --out figs/runtime.png
    python plot_experiment_runtimes.py --ignore-manual
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

REPO = Path(__file__).resolve().parent

NEW_NB = REPO / "ES-008-BC_2-1_8853_CD1.ipynb"   # new, workflow based script
FALLBACK_NB = REPO / "Untitled.ipynb"            # used when NEW_NB has no data
OLD_NB = REPO / "S3_Q2_Cooldown_2.ipynb"         # old script

OLD_LABEL = "Old script (S3_Q2_Cooldown_2)"
NEW_LABEL = "New workflow (ES-008-BC_2-1_8853_CD1)"

OLD_COLOR = "0.6"        # grey
NEW_COLOR = "#FF1111"    # bright red

# Save the figure without a background, so it can be dropped on any slide.
TRANSPARENT_BACKGROUND = True

# Below this wall time a run is considered emulated rather than measured, and
# the compiler's RT estimate is used instead.
MIN_WALL_TIME_S = 1.0


@dataclass(frozen=True)
class Experiment:
    """One experiment and how to find it in each of the notebooks."""

    key: str              # short name, used in MANUAL_TIMES
    label: str            # x-axis label ('\n' allowed)
    heading_new: str      # heading regex in NEW_NB
    heading_fallback: str # heading regex in FALLBACK_NB
    heading_old: str      # heading regex in OLD_NB


# Experiments in plotting order.
EXPERIMENTS: list[Experiment] = [
    Experiment("resonator_spectroscopy", "Resonator\nspectroscopy",
               r"Resonator Spectroscopy", r"Resonator Spectroscopy", r"Pulsed Resonator Spectroscopy"),
    Experiment("qubit_spectroscopy", "Qubit\nspectroscopy",
               r"Qubit Spectroscopy", r"Qubit Spectroscopy", r"Pulsed Qubit Spectroscopy"),
    Experiment("amplitude_rabi", "Amplitude\nRabi",
               r"Amplitude Rabi", r"Amplitude Rabi", r"Amplitude Rabi Experiment"),
    Experiment("ramsey", "Ramsey",
               r"Ramsey", r"Ramsey", r"Ramsey Experiments"),
    Experiment("t1", "T1\nlifetime",
               r"T1 Lifetime", r"T1", r"T1 Experiment"),
    Experiment("drag", "DRAG\ncalibration",
               r"DRAG Calibration", r"DRAG Calibration", r"DRAG Calibration"),
    Experiment("hahn_echo", "Hahn\necho",
               r"Hahn.?Echo", r"Echo", r"Hahn Echo Experiment"),
]

# --------------------------------------------------------------------------- #
# Manual running times -- EDIT THIS TABLE
# --------------------------------------------------------------------------- #
#
# Running times in seconds that should be used instead of the ones extracted
# from the notebooks.  Keys are the ``Experiment.key`` values above:
#
#     resonator_spectroscopy, qubit_spectroscopy, amplitude_rabi, ramsey,
#     t1, drag, hahn_echo
#
# "old" is the grey bar (S3_Q2_Cooldown_2), "new" is the red bar (ES-008).
# Give only the entries you want to override, drop or comment out the rest.
# Setting a value to ``None`` removes the bar entirely (plotted as "n/a").
#
# Examples:
#     "hahn_echo": {"new": 42.8},          # new value only, old one scraped
#     "drag": {"old": 12.5, "new": 118.5}, # both bars set by hand
#     "ramsey": {"old": None},             # hide the old bar
#
MANUAL_TIMES: dict[str, dict[str, float | None]] = {
    "resonator_spectroscopy": {"old": 20.9, "new": 10.22},
    "qubit_spectroscopy":     {"old": 261.2, "new": 10.46},
    "amplitude_rabi":         {"old": 58.0, "new": 28.65},
    "ramsey":                 {"old": 214.5, "new": 87.7},
    "t1":                     {"old": 228.1, "new": 72.43},
    "drag":                   {"old": None, "new": 118.37},
    "hahn_echo":              {"old": 373.1, "new": 42.8},
}

# --------------------------------------------------------------------------- #
# Notebook parsing
# --------------------------------------------------------------------------- #

HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.*\S)\s*$")
LOG_LINE_RE = re.compile(
    r"\[(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\.(\d{3})\]([^\n]*)"
)
RT_ESTIMATE_RE = re.compile(r"Estimated RT execution time:\s*([\d.]+)\s*s")
START_MARKER = "Starting near-time execution"
FINISH_MARKER = "Finished near-time execution"


@dataclass
class Timing:
    """Runtime of a single experiment execution."""

    seconds: float
    source: str                    # "wall", "rt-estimate" or "manual"
    notebook: str | None = None
    cell_index: int | None = None

    @property
    def marker(self) -> str:
        """Suffix appended to the bar label.

        Manual values are drawn as plain bars; only a compiler RT estimate,
        which is not a measured time, is flagged.
        """
        return {"rt-estimate": "*"}.get(self.source, "")

    @property
    def hatch(self) -> str:
        """Hatch pattern marking a value that was not measured on hardware."""
        return {"rt-estimate": "//"}.get(self.source, "")

    @property
    def origin(self) -> str:
        if self.source == "manual":
            return "MANUAL_TIMES"
        return f"{self.notebook} cell {self.cell_index} ({self.source})"


def cell_output_text(cell: dict) -> str:
    """Concatenate every textual output of a code cell."""
    chunks: list[str] = []
    for output in cell.get("outputs", []):
        if "text" in output:                                # stream output
            chunks.append("".join(output["text"]))
        plain = output.get("data", {}).get("text/plain")     # execute_result
        if plain:
            chunks.append("".join(plain))
    return "\n".join(chunks)


def parse_timestamp(match: re.Match) -> dt.datetime:
    year, month, day, hour, minute, second, milli = (int(g) for g in match.groups()[:7])
    return dt.datetime(year, month, day, hour, minute, second, milli * 1000)


def timing_from_cell(text: str) -> tuple[float | None, float | None]:
    """Return ``(wall_time, rt_estimate)`` in seconds for one cell output."""
    start = finish = None
    for match in LOG_LINE_RE.finditer(text):
        message = match.group(8)
        if start is None and START_MARKER in message:
            start = parse_timestamp(match)
        if FINISH_MARKER in message:
            finish = parse_timestamp(match)

    wall = None
    if start is not None and finish is not None and finish >= start:
        wall = (finish - start).total_seconds()

    rt_matches = RT_ESTIMATE_RE.findall(text)
    rt = float(rt_matches[0]) if rt_matches else None
    return wall, rt


def section_cells(cells: list[dict], heading_pattern: str) -> list[tuple[int, dict]]:
    """Code cells belonging to the first section whose heading matches.

    A section ends at the next heading of the same or a higher level.
    """
    pattern = re.compile(heading_pattern, re.IGNORECASE)
    level: int | None = None
    collected: list[tuple[int, dict]] = []

    for index, cell in enumerate(cells):
        source = "".join(cell["source"])

        if cell["cell_type"] == "markdown":
            for line in source.splitlines():
                heading = HEADING_RE.match(line)
                if not heading:
                    continue
                depth, title = len(heading.group(1)), heading.group(2)
                if level is None:
                    if pattern.search(title):
                        level = depth
                elif depth <= level:
                    return collected           # section finished
            continue

        if level is not None and cell["cell_type"] == "code":
            collected.append((index, cell))

    return collected


def experiment_timing(notebook: Path, heading_pattern: str) -> Timing | None:
    """Timing of the first executed measurement inside a notebook section."""
    cells = json.loads(notebook.read_text())["cells"]

    for index, cell in section_cells(cells, heading_pattern):
        wall, rt = timing_from_cell(cell_output_text(cell))

        if wall is not None and wall >= MIN_WALL_TIME_S:
            return Timing(wall, "wall", notebook.name, index)
        if rt is not None:
            # Emulated run (or a cell where only the compiler report survived).
            return Timing(rt, "rt-estimate", notebook.name, index)

    return None


def validate_manual_times() -> None:
    """Fail early on typos in the hand-edited table."""
    known = {experiment.key for experiment in EXPERIMENTS}
    for key, entry in MANUAL_TIMES.items():
        if key not in known:
            raise KeyError(
                f"MANUAL_TIMES has unknown experiment {key!r}; "
                f"expected one of {sorted(known)}"
            )
        unknown_columns = set(entry) - {"old", "new"}
        if unknown_columns:
            raise KeyError(
                f"MANUAL_TIMES[{key!r}] has unknown key(s) "
                f"{sorted(unknown_columns)}; expected 'old' and/or 'new'"
            )


def manual_override(key: str, column: str, scraped: Timing | None) -> Timing | None:
    """Replace a scraped timing by the hand-edited one, when there is one."""
    entry = MANUAL_TIMES.get(key, {})
    if column not in entry:
        return scraped
    seconds = entry[column]
    return None if seconds is None else Timing(float(seconds), "manual")


def collect_timings(use_manual: bool = True) -> list[tuple[Experiment, Timing | None, Timing | None]]:
    """``(experiment, old timing, new timing)`` for every experiment."""
    if use_manual:
        validate_manual_times()

    rows = []
    for experiment in EXPERIMENTS:
        new = experiment_timing(NEW_NB, experiment.heading_new)
        if new is None:
            new = experiment_timing(FALLBACK_NB, experiment.heading_fallback)
        old = experiment_timing(OLD_NB, experiment.heading_old)

        if use_manual:
            old = manual_override(experiment.key, "old", old)
            new = manual_override(experiment.key, "new", new)

        rows.append((experiment, old, new))
    return rows


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #

def annotate(ax: plt.Axes, x: float, timing: Timing | None, log: bool) -> None:
    """Put the runtime (or ``n/a``) above a bar."""
    if timing is None:
        bottom = ax.get_ylim()[0] if log else 0.0
        ax.text(x, bottom, " n/a ", ha="center", va="bottom",
                fontsize=8, color="0.35", rotation=90)
        return

    label = f"{timing.seconds:.1f} s{timing.marker}"
    offset = 1.05 if log else 1.0
    ax.text(x, timing.seconds * offset if log else timing.seconds + 8,
            label, ha="center", va="bottom", fontsize=8.5)


def plot(rows, out_path: Path, log: bool = False) -> None:
    names = [experiment.label for experiment, _, _ in rows]
    positions = np.arange(len(rows), dtype=float)
    width = 0.38

    figure, ax = plt.subplots(figsize=(11, 6))

    for offset, color, label, column in (
        (-width / 2, OLD_COLOR, OLD_LABEL, 1),
        (+width / 2, NEW_COLOR, NEW_LABEL, 2),
    ):
        xs, heights, hatches = [], [], []
        for position, row in zip(positions, rows):
            timing = row[column]
            if timing is None:
                continue
            xs.append(position + offset)
            heights.append(timing.seconds)
            hatches.append(timing.hatch)

        bars = ax.bar(xs, heights, width, color=color, label=label,
                      edgecolor="black", linewidth=0.6, zorder=3)
        for bar, hatch in zip(bars, hatches):
            if hatch:
                bar.set_hatch(hatch)

    if log:
        ax.set_yscale("log")

    for position, row in zip(positions, rows):
        annotate(ax, position - width / 2, row[1], log)
        annotate(ax, position + width / 2, row[2], log)

    ax.set_xticks(positions)
    ax.set_xticklabels(names)
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Running time (s)")
    ax.set_title("Measurement running time per experiment: old script vs. new workflow")
    ax.legend(loc="upper left", frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    if not log:
        ax.margins(y=0.14)

    sources = {t.source for row in rows for t in row[1:] if t is not None}
    if "rt-estimate" in sources:
        figure.text(0.99, 0.015,
                    "*  hatched: no hardware run available, compiler RT estimate used",
                    ha="right", va="bottom", fontsize=8, color="0.3")

    figure.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, dpi=200, transparent=TRANSPARENT_BACKGROUND)
    print(f"\nfigure written to {out_path}")


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def report(rows) -> None:
    header = (f"{'experiment':22s} {'old [s]':>9s} {'new [s]':>9s} {'speed-up':>9s}"
              f"   source of the new value")
    print(header)
    print("-" * len(header))

    for experiment, old, new in rows:
        flat = experiment.label.replace("\n", " ")
        old_text = f"{old.seconds:9.1f}" if old else f"{'n/a':>9s}"
        new_text = f"{new.seconds:9.1f}" if new else f"{'n/a':>9s}"
        speedup = f"{old.seconds / new.seconds:8.2f}x" if old and new else f"{'-':>9s}"
        print(f"{flat:22s} {old_text} {new_text} {speedup}   "
              f"{new.origin if new else '-'}")

    totals = [(o, n) for _, o, n in rows if o and n]
    if totals:
        old_total = sum(o.seconds for o, _ in totals)
        new_total = sum(n.seconds for _, n in totals)
        print("-" * len(header))
        print(f"{'total (shared only)':22s} {old_total:9.1f} {new_total:9.1f} "
              f"{old_total / new_total:8.2f}x")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=REPO / "experiment_runtime_comparison.png",
                        help="output image path")
    parser.add_argument("--log", action="store_true",
                        help="use a logarithmic time axis")
    parser.add_argument("--ignore-manual", action="store_true",
                        help="ignore MANUAL_TIMES and only use the notebooks")
    args = parser.parse_args()

    rows = collect_timings(use_manual=not args.ignore_manual)
    report(rows)
    plot(rows, args.out, log=args.log)


if __name__ == "__main__":
    main()
