#!/usr/bin/env python3
"""Export CSV data as a browser-friendly JS payload for file:// previews."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VISUAL_DATA = ROOT / "visuals" / "data.js"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    current_results = read_csv(ROOT / "data" / "current_results_clean.csv")
    candidate_results = read_csv(ROOT / "data" / "current_candidate_results.csv")
    historical_summary = read_csv(ROOT / "data" / "historical_election_summary.csv")
    payload = (
        "window.TN_CURRENT_RESULTS = "
        + json.dumps(current_results, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
        + "window.TN_CANDIDATE_RESULTS = "
        + json.dumps(candidate_results, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
        + "window.TN_HISTORICAL_SUMMARY = "
        + json.dumps(historical_summary, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    VISUAL_DATA.write_text(payload, encoding="utf-8")
    print(f"Wrote {VISUAL_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
