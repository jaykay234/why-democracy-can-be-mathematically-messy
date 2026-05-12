#!/usr/bin/env python3
"""Validate generated TN 2026 CSV datasets."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_CSV = ROOT / "data" / "current_results_clean.csv"
MAPPING_CSV = ROOT / "data" / "district_constituency_mapping.csv"
HISTORICAL_CSV = ROOT / "data" / "historical_election_summary.csv"

EXPECTED_PARTY_TOTALS = {
    "TVK": 108,
    "DMK": 59,
    "ADMK": 47,
    "INC": 5,
    "PMK": 4,
    "IUML": 2,
    "CPI": 2,
    "VCK": 2,
    "CPI(M)": 2,
    "BJP": 1,
    "DMDK": 1,
    "AMMKMNKZ": 1,
}

EXPECTED_HISTORICAL_YEARS = [
    1967,
    1971,
    1977,
    1980,
    1984,
    1989,
    1991,
    1996,
    2001,
    2006,
    2011,
    2016,
    2021,
    2026,
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_results(rows: list[dict[str, str]]) -> None:
    require(len(rows) == 234, f"current_results_clean.csv must have 234 rows, found {len(rows)}")

    constituency_numbers = sorted(int(row["constituency_no"]) for row in rows)
    require(
        constituency_numbers == list(range(1, 235)),
        "constituency_no must be unique and cover 1..234",
    )

    party_totals = Counter(row["winner_party"] for row in rows)
    require(
        dict(party_totals) == EXPECTED_PARTY_TOTALS,
        f"party totals mismatch: {dict(party_totals)}",
    )

    for row in rows:
        require(row["district"], f"missing district for AC {row['constituency_no']}")
        require(row["source_url"], f"missing source_url for AC {row['constituency_no']}")
        require(row["source_last_updated"], f"missing source_last_updated for AC {row['constituency_no']}")
        require(row["data_version"], f"missing data_version for AC {row['constituency_no']}")
        margin = int(row["margin"])
        vote_margin = int(row["winner_votes"]) - int(row["runnerup_votes"])
        require(
            margin == vote_margin,
            f"margin mismatch for AC {row['constituency_no']}: {margin} != {vote_margin}",
        )

    chennai_count = sum(1 for row in rows if row["district"] == "Chennai")
    require(chennai_count == 16, f"Chennai must have 16 constituencies, found {chennai_count}")


def validate_mapping(rows: list[dict[str, str]]) -> None:
    require(len(rows) == 234, f"district_constituency_mapping.csv must have 234 rows, found {len(rows)}")
    constituency_numbers = sorted(int(row["constituency_no"]) for row in rows)
    require(
        constituency_numbers == list(range(1, 235)),
        "mapping constituency_no must be unique and cover 1..234",
    )
    for row in rows:
        require(row["administrative_district"], f"missing district for AC {row['constituency_no']}")
        require(row["mapping_source_url"], f"missing mapping source for AC {row['constituency_no']}")
        require(row["mapping_verified_on"], f"missing mapping verification date for AC {row['constituency_no']}")

    chennai_count = sum(1 for row in rows if row["administrative_district"] == "Chennai")
    require(chennai_count == 16, f"mapping Chennai count must be 16, found {chennai_count}")


def validate_historical(rows: list[dict[str, str]]) -> None:
    years = [int(row["year"]) for row in rows]
    require(years == EXPECTED_HISTORICAL_YEARS, f"historical years mismatch: {years}")

    for row in rows:
        total = int(row["total_seats"])
        seats = (
            int(row["first_seats"])
            + int(row["second_seats"])
            + int(row["third_seats"])
            + int(row["other_seats"])
        )
        require(total == 234, f"historical total_seats must be 234 for {row['year']}")
        require(seats == total, f"historical seat groups must sum to {total} for {row['year']}")
        require(row["first_pole"], f"missing first pole for {row['year']}")
        require(row["second_pole"], f"missing second pole for {row['year']}")
        require(row["third_pole"], f"missing third pole for {row['year']}")
        require(row["pattern"], f"missing pattern for {row['year']}")
        require(row["source_url"], f"missing source_url for {row['year']}")

    row_2026 = next(row for row in rows if int(row["year"]) == 2026)
    require(row_2026["first_pole"] == "TVK", "2026 first pole should be TVK")
    require(int(row_2026["first_seats"]) == EXPECTED_PARTY_TOTALS["TVK"], "2026 TVK historical seats mismatch")
    require(int(row_2026["second_seats"]) == EXPECTED_PARTY_TOTALS["DMK"], "2026 DMK historical seats mismatch")
    require(int(row_2026["third_seats"]) == EXPECTED_PARTY_TOTALS["ADMK"], "2026 ADMK historical seats mismatch")


def main() -> int:
    result_rows = read_csv(RESULTS_CSV)
    mapping_rows = read_csv(MAPPING_CSV)
    historical_rows = read_csv(HISTORICAL_CSV)
    validate_results(result_rows)
    validate_mapping(mapping_rows)
    validate_historical(historical_rows)
    print("Validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
