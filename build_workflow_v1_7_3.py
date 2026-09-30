"""Build `Workflow-v1.7.3.ipynb` from `new_single_shot.py`.

`Workflow-v1.7.3.ipynb` is identical to `ES-011-A_19312_2-2_Q3_CD1_1.json`
except that the whole "Single Shot 0 and 1 Measurements" section (from the
"# Single Shot 0 and 1 Measurements" header up to, and including, the last
cell before the next top-level "# ..." section) is replaced by the cells
defined in `new_single_shot.py`.

`new_single_shot.py` is written in the jupytext "percent" format: every
`# %%` (code cell) or `# %% [markdown]` (markdown cell) line starts a new
notebook cell. This script contains a small, dependency-free parser for that
format so it does not require `jupytext` to be installed.

Usage:
    python build_workflow_v1_7_3.py
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
BASE_NOTEBOOK_PATH = REPO_DIR / "ES-011-A_19312_2-2_Q3_CD1_1.json"
SINGLE_SHOT_SCRIPT_PATH = REPO_DIR / "new_single_shot.py"
OUTPUT_NOTEBOOK_PATH = REPO_DIR / "Workflow-v1.7.3.ipynb"

# Markdown/code header and footer used to locate the section being replaced.
SECTION_START_MARKER = "# Single Shot 0 and 1 Measurements"
NEXT_SECTION_PREFIX = "# "  # any other top-level "# ..." markdown header


def parse_percent_format(script_text: str) -> list[dict]:
    """Parse a jupytext "percent"-format script into notebook cell dicts.

    Each returned dict has keys "cell_type" ("code" or "markdown") and
    "source" (a single string, without a trailing newline on the last line).
    """
    lines = script_text.split("\n")
    n = len(lines)
    i = 0
    # Skip the file header (everything before the first cell marker).
    while i < n and not lines[i].startswith("# %%"):
        i += 1

    cells = []
    while i < n:
        marker = lines[i]
        is_markdown = "[markdown]" in marker
        i += 1

        content_lines = []
        while i < n and not lines[i].startswith("# %%"):
            content_lines.append(lines[i])
            i += 1

        if is_markdown:
            md_lines = []
            for line in content_lines:
                if line == "#":
                    md_lines.append("")
                elif line.startswith("# "):
                    md_lines.append(line[2:])
                else:
                    md_lines.append(line)
            while md_lines and md_lines[-1] == "":
                md_lines.pop()
            source = "\n".join(md_lines)
        else:
            code_lines = list(content_lines)
            while code_lines and code_lines[-1] == "":
                code_lines.pop()
            source = "\n".join(code_lines)

        cells.append({"cell_type": "markdown" if is_markdown else "code", "source": source})

    return cells


def to_notebook_cell(cell: dict) -> dict:
    """Turn a {"cell_type", "source"} dict into a full notebook cell dict."""
    source_lines = cell["source"].splitlines(keepends=True)
    if cell["cell_type"] == "code":
        return {
            "cell_type": "code",
            "execution_count": None,
            "id": str(uuid.uuid4()),
            "metadata": {},
            "outputs": [],
            "source": source_lines,
        }
    return {
        "cell_type": "markdown",
        "id": str(uuid.uuid4()),
        "metadata": {},
        "source": source_lines,
    }


def find_section_bounds(cells: list[dict]) -> tuple[int, int]:
    """Return the [start, end) cell-index range of the section being replaced."""
    start = None
    for i, cell in enumerate(cells):
        source = "".join(cell.get("source", []))
        if cell["cell_type"] == "markdown" and source.startswith(SECTION_START_MARKER):
            start = i
            break
    if start is None:
        raise ValueError(f"Could not find section header {SECTION_START_MARKER!r}")

    end = None
    for i in range(start + 1, len(cells)):
        cell = cells[i]
        source = "".join(cell.get("source", []))
        is_top_level_header = source.startswith(NEXT_SECTION_PREFIX) and not source.startswith("## ")
        if cell["cell_type"] == "markdown" and is_top_level_header:
            end = i
            break
    if end is None:
        raise ValueError("Could not find the start of the next top-level section")
    return start, end


def main() -> None:
    base_notebook = json.loads(BASE_NOTEBOOK_PATH.read_text())
    script_text = SINGLE_SHOT_SCRIPT_PATH.read_text()

    new_cells_raw = parse_percent_format(script_text)
    new_cells = [to_notebook_cell(c) for c in new_cells_raw]

    cells = base_notebook["cells"]
    start, end = find_section_bounds(cells)
    print(f"Replacing cells [{start}, {end}) ({end - start} cells) with "
          f"{len(new_cells)} new cells parsed from {SINGLE_SHOT_SCRIPT_PATH.name}")

    base_notebook["cells"] = cells[:start] + new_cells + cells[end:]

    OUTPUT_NOTEBOOK_PATH.write_text(json.dumps(base_notebook, indent=1))
    print(f"Wrote {OUTPUT_NOTEBOOK_PATH} with {len(base_notebook['cells'])} cells")


if __name__ == "__main__":
    main()
