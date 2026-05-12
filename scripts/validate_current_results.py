#!/usr/bin/env python3
"""Validate the CSV-only Tamil Nadu 2026 current results dataset."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


TOTAL_SEATS = 234
EXPECTED_CONSTITUENCY_NOS = set(range(1, TOTAL_SEATS + 1))
EXPECTED_PARTY_SEATS = {
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
REQUIRED_COLUMNS = {
    "constituency_no",
    "constituency_name",
    "district",
    "winner_party",
    "winner_votes",
    "runnerup_votes",
    "margin",
    "source_url",
    "source_last_updated",
    "data_version",
}
REQUIRED_POPULATED_COLUMNS = ("source_url", "source_last_updated", "data_version")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate data/current_results_clean.csv for the TN 2026 election analysis."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="data/current_results_clean.csv",
        help="Path to current_results_clean.csv. Defaults to data/current_results_clean.csv.",
    )
    return parser.parse_args()


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_int(value: str, field: str, row_number: int, errors: list[str]) -> int | None:
    text = clean(value).replace(",", "")
    if not text:
        return None

    try:
        parsed = Decimal(text)
    except InvalidOperation:
        errors.append(f"Row {row_number}: {field} is not numeric: {value!r}")
        return None

    if parsed != parsed.to_integral_value():
        errors.append(f"Row {row_number}: {field} must be a whole number: {value!r}")
        return None

    return int(parsed)


def load_rows(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []

    if not csv_path.exists():
        return [], [f"CSV file not found: {csv_path}"]

    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        rows = list(reader)

    return rows, errors


def validate_row_count(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != TOTAL_SEATS:
        errors.append(f"Expected exactly {TOTAL_SEATS} rows, found {len(rows)}")


def validate_constituencies(rows: list[dict[str, str]], errors: list[str]) -> None:
    constituency_nos: list[int] = []
    seen_by_no: dict[int, list[int]] = defaultdict(list)

    for index, row in enumerate(rows, start=2):
        constituency_no = parse_int(row.get("constituency_no", ""), "constituency_no", index, errors)
        if constituency_no is None:
            continue

        constituency_nos.append(constituency_no)
        seen_by_no[constituency_no].append(index)

    duplicates = {number: row_numbers for number, row_numbers in seen_by_no.items() if len(row_numbers) > 1}
    if duplicates:
        details = ", ".join(
            f"{number} on rows {row_numbers}" for number, row_numbers in sorted(duplicates.items())
        )
        errors.append(f"constituency_no must be unique; duplicates found: {details}")

    actual_nos = set(constituency_nos)
    missing = sorted(EXPECTED_CONSTITUENCY_NOS - actual_nos)
    unexpected = sorted(actual_nos - EXPECTED_CONSTITUENCY_NOS)
    if missing:
        errors.append(f"Missing constituency_no values: {format_number_list(missing)}")
    if unexpected:
        errors.append(f"Unexpected constituency_no values outside 1..{TOTAL_SEATS}: {format_number_list(unexpected)}")


def validate_districts(rows: list[dict[str, str]], errors: list[str]) -> None:
    districts_by_constituency: dict[int, set[str]] = defaultdict(set)
    chennai_constituencies: set[int] = set()

    for index, row in enumerate(rows, start=2):
        district = clean(row.get("district", ""))
        if not district:
            errors.append(f"Row {index}: district must be populated")

        constituency_no = parse_int(row.get("constituency_no", ""), "constituency_no", index, errors)
        if constituency_no is None:
            continue

        districts_by_constituency[constituency_no].add(district)
        if district == "Chennai":
            chennai_constituencies.add(constituency_no)

    multi_district = {
        number: sorted(districts)
        for number, districts in districts_by_constituency.items()
        if len(districts) != 1 or "" in districts
    }
    if multi_district:
        details = ", ".join(
            f"{number}: {districts}" for number, districts in sorted(multi_district.items())
        )
        errors.append(f"Each constituency must have exactly one populated district; issues: {details}")

    if len(chennai_constituencies) != 16:
        errors.append(
            "Chennai administrative district must contain exactly 16 constituencies; "
            f"found {len(chennai_constituencies)}"
        )


def validate_party_totals(rows: list[dict[str, str]], errors: list[str]) -> None:
    party_counts = Counter(clean(row.get("winner_party", "")) for row in rows)
    if "" in party_counts:
        errors.append(f"winner_party must be populated; found {party_counts['']} blank row(s)")
        del party_counts[""]

    expected = Counter(EXPECTED_PARTY_SEATS)
    if party_counts != expected:
        mismatch_lines = []
        all_parties = sorted(set(party_counts) | set(expected))
        for party in all_parties:
            actual_count = party_counts.get(party, 0)
            expected_count = expected.get(party, 0)
            if actual_count != expected_count:
                mismatch_lines.append(f"{party}: expected {expected_count}, found {actual_count}")
        errors.append("Party seat totals do not match expected values: " + "; ".join(mismatch_lines))


def validate_margins(rows: list[dict[str, str]], errors: list[str]) -> None:
    for index, row in enumerate(rows, start=2):
        winner_votes = clean(row.get("winner_votes", ""))
        runnerup_votes = clean(row.get("runnerup_votes", ""))
        margin = clean(row.get("margin", ""))

        if not winner_votes or not runnerup_votes or not margin:
            continue

        winner_value = parse_int(winner_votes, "winner_votes", index, errors)
        runnerup_value = parse_int(runnerup_votes, "runnerup_votes", index, errors)
        margin_value = parse_int(margin, "margin", index, errors)

        if winner_value is None or runnerup_value is None or margin_value is None:
            continue

        expected_margin = winner_value - runnerup_value
        if margin_value != expected_margin:
            constituency = clean(row.get("constituency_no", "unknown"))
            errors.append(
                f"Row {index} constituency {constituency}: margin expected {expected_margin} "
                f"from winner_votes-runnerup_votes, found {margin_value}"
            )


def validate_metadata(rows: list[dict[str, str]], errors: list[str]) -> None:
    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_POPULATED_COLUMNS:
            if not clean(row.get(column, "")):
                errors.append(f"Row {index}: {column} must be populated")


def format_number_list(numbers: list[int]) -> str:
    preview = ", ".join(str(number) for number in numbers[:25])
    if len(numbers) > 25:
        return f"{preview}, ... ({len(numbers)} total)"
    return preview


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv_path)
    rows, errors = load_rows(csv_path)

    if rows:
        validate_row_count(rows, errors)
        validate_constituencies(rows, errors)
        validate_districts(rows, errors)
        validate_party_totals(rows, errors)
        validate_margins(rows, errors)
        validate_metadata(rows, errors)

    if errors:
        print(f"Validation failed for {csv_path}:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed for {csv_path}: {len(rows)} constituency rows checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
