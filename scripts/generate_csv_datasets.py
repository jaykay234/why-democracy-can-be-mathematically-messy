#!/usr/bin/env python3
"""Generate the TN 2026 CSV datasets from public ECI result pages."""

from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026"
WIKI_MAPPING_URL = (
    "https://en.wikipedia.org/wiki/"
    "List_of_constituencies_of_the_Tamil_Nadu_Legislative_Assembly"
)
STATE = "Tamil Nadu"
YEAR = "2026"
DATA_VERSION = "official_public_snapshot_2026_05_05_1618"
MAPPING_VERIFIED_ON = "2026-05-12"
SOURCE_LAST_UPDATED_FALLBACK = "04:18 PM On 05/05/2026"

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RESULTS_CSV = DATA_DIR / "current_results_clean.csv"
MAPPING_CSV = DATA_DIR / "district_constituency_mapping.csv"
CANDIDATES_CSV = DATA_DIR / "current_candidate_results.csv"

PARTY_ABBREVIATIONS = {
    "Aanaithinthiya Jananayaka Pathukappu Kazhagam": "AJPK",
    "All India Anna Dravida Munnetra Kazhagam": "ADMK",
    "All India Forward Bloc": "AIFB",
    "All India Majlis-E-Ittehadul Muslimeen": "AIMIM",
    "All India Puratchi Thalaivar Makkal Munnettra Kazhagam": "AIPTMMK",
    "Amma Makkal Munnettra Kazagam": "AMMKMNKZ",
    "Bahujan Samaj Party": "BSP",
    "Bharatiya Janata Party": "BJP",
    "Communist Party of India": "CPI",
    "Communist Party of India (Marxist)": "CPI(M)",
    "Communist Party of India (Marxist-Leninist) Red Star": "CPI(ML)RS",
    "Desiya Makkal Sakthi Katchi": "DMSK",
    "Desiya Murpokku Dravida Kazhagam": "DMDK",
    "Dravida Munnetra Kazhagam": "DMK",
    "Ganasangam Party of India": "GSPI",
    "Independent": "IND",
    "Indian National Congress": "INC",
    "Indian Union Muslim League": "IUML",
    "Indhu Dravida Makkal Katchi": "IDMK",
    "Naam Indiar Party": "NIP",
    "Naam Tamilar Katchi": "NTK",
    "None of the Above": "NOTA",
    "Pattali Makkal Katchi": "PMK",
    "Puthiya Tamilagam": "PT",
    "Samaniya Makkal Nala Katchi": "SMNK",
    "Samata Party": "SAP",
    "Tamilaga Vettri Kazhagam": "TVK",
    "Tamizhaga Vaazhvurimai Katchi": "TVKATCHI",
    "Veerath Thiyagi Viswanathadoss Thozhilalarkal Katchi": "VTVTK",
    "Viduthalai Chiruthaigal Katchi": "VCK",
}

CHENNAI_URBAN_BELT_CONSTITUENCIES = {
    5,
    6,
    7,
    8,
    9,
    10,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
}

ADMIN_DISTRICT_OVERRIDES = {
    7: "Thiruvallur",
    8: "Thiruvallur",
    9: "Thiruvallur",
    10: "Thiruvallur",
    27: "Chengalpattu",
    28: "Chengalpattu",
}

ADMIN_DISTRICT_OVERRIDE_NOTES = {
    7: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
    8: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
    9: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
    10: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
    27: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
    28: "Administrative district corrected from broad Chennai grouping; part of Chennai Urban Belt.",
}


@dataclass(frozen=True)
class Cell:
    text: str
    rowspan: int = 1
    colspan: int = 1
    is_header: bool = False


class TableParser(HTMLParser):
    """Collect HTML tables while keeping nested-table text out of parent cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._tables: list[dict] = []
        self.tables: list[list[list[Cell]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key: value or "" for key, value in attrs}
        if tag == "table":
            self._tables.append({"rows": [], "row": None, "cell": None, "attrs": attrs_map})
            return

        if not self._tables:
            return

        current = self._tables[-1]
        if tag == "tr":
            current["row"] = []
        elif tag in {"td", "th"} and current["row"] is not None:
            current["cell"] = {
                "parts": [],
                "rowspan": int(attrs_map.get("rowspan") or 1),
                "colspan": int(attrs_map.get("colspan") or 1),
                "is_header": tag == "th",
            }

    def handle_data(self, data: str) -> None:
        if not self._tables:
            return
        current = self._tables[-1]
        if current["cell"] is not None:
            current["cell"]["parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._tables:
            return

        current = self._tables[-1]
        if tag in {"td", "th"} and current["cell"] is not None:
            text = clean_text(" ".join(current["cell"]["parts"]))
            current["row"].append(
                Cell(
                    text=text,
                    rowspan=current["cell"]["rowspan"],
                    colspan=current["cell"]["colspan"],
                    is_header=current["cell"]["is_header"],
                )
            )
            current["cell"] = None
        elif tag == "tr" and current["row"] is not None:
            if current["row"]:
                current["rows"].append(current["row"])
            current["row"] = None
        elif tag == "table":
            completed = self._tables.pop()
            self.tables.append(completed["rows"])


def clean_text(value: str) -> str:
    return html.unescape(value).replace("\xa0", " ").strip()


def fetch(url: str, retries: int = 3) -> str:
    try:
        completed = subprocess.run(
            ["curl", "-L", "--silent", "--show-error", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=45,
        )
        if completed.stdout.strip():
            return completed.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; TN-2026-analysis-dataset/1.0; "
                "+https://results.eci.gov.in/)"
            )
        },
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1 + attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def parse_tables(markup: str) -> list[list[list[Cell]]]:
    parser = TableParser()
    parser.feed(markup)
    return parser.tables


def expand_rowspans(table: list[list[Cell]]) -> list[list[str]]:
    expanded: list[list[str]] = []
    spans: dict[int, list] = {}
    for row in table:
        out: list[str] = []
        col = 0
        for cell in row:
            while col in spans:
                text, remaining = spans[col]
                out.append(text)
                remaining -= 1
                if remaining:
                    spans[col] = [text, remaining]
                else:
                    del spans[col]
                col += 1

            for _ in range(cell.colspan):
                out.append(cell.text)
                if cell.rowspan > 1:
                    spans[col] = [cell.text, cell.rowspan - 1]
                col += 1

        while col in spans:
            text, remaining = spans[col]
            out.append(text)
            remaining -= 1
            if remaining:
                spans[col] = [text, remaining]
            else:
                del spans[col]
            col += 1
        expanded.append(out)
    return expanded


def extract_last_updated(markup: str) -> str:
    match = re.search(r"Last Updated at\s*<span>([^<]+)</span>", markup)
    if match:
        return clean_text(match.group(1))
    match = re.search(r"Last Updated at\s+([^<\n]+)", markup)
    return clean_text(match.group(1)) if match else SOURCE_LAST_UPDATED_FALLBACK


def party_code(party_name: str) -> str:
    return PARTY_ABBREVIATIONS.get(party_name, party_name)


def find_summary_table(markup: str) -> list[list[str]]:
    for table in parse_tables(markup):
        rows = [[cell.text for cell in row] for row in table]
        if any(row[:2] == ["Constituency", "Const. No."] for row in rows):
            return rows
    raise RuntimeError("Could not find ECI constituency summary table")


def parse_summary_pages() -> tuple[dict[int, dict[str, str]], str]:
    summaries: dict[int, dict[str, str]] = {}
    source_last_updated = SOURCE_LAST_UPDATED_FALLBACK
    for page_no in range(1, 13):
        suffix = str(page_no) if page_no < 10 else f"1{page_no % 10}"
        url = f"{BASE_URL}/statewiseS22{suffix}.htm"
        markup = fetch(url)
        if page_no == 1:
            source_last_updated = extract_last_updated(markup)
        table = find_summary_table(markup)
        for row in table:
            if len(row) != 9 or not row[1].isdigit():
                continue
            constituency_no = int(row[1])
            summaries[constituency_no] = {
                "constituency_name": row[0],
                "winner_candidate": row[2],
                "winner_party_full": row[3],
                "runnerup_candidate": row[4],
                "runnerup_party_full": row[5],
                "summary_margin": row[6],
                "round": row[7],
                "result_status": row[8],
            }
    return summaries, source_last_updated


def find_candidate_table(markup: str) -> list[list[str]]:
    for table in parse_tables(markup):
        rows = [[cell.text for cell in row] for row in table]
        if any(row[:3] == ["S.N.", "Candidate", "Party"] for row in rows):
            return rows
    raise RuntimeError("Could not find ECI candidate table")


def parse_int(value: str) -> int:
    return int(value.replace(",", "").strip())


def parse_float(value: str) -> float:
    return float(value.replace(",", "").strip())


def parse_candidate_page(constituency_no: int) -> dict[str, object]:
    url = f"{BASE_URL}/ConstituencywiseS22{constituency_no}.htm"
    markup = fetch(url)
    table = find_candidate_table(markup)
    candidates: list[dict[str, object]] = []
    total_votes = 0
    for row in table:
        if not row:
            continue
        if row[0].isdigit() and len(row) >= 7:
            candidates.append(
                {
                    "candidate": row[1],
                    "party_full": row[2],
                    "party": party_code(row[2]),
                    "evm_votes": parse_int(row[3]),
                    "postal_votes": parse_int(row[4]),
                    "total_votes": parse_int(row[5]),
                    "vote_share": parse_float(row[6]),
                }
            )
        elif len(row) >= 6 and row[1] == "Total":
            total_votes = parse_int(row[5])

    ranked = sorted(
        [item for item in candidates if item["party_full"] != "None of the Above"],
        key=lambda item: item["total_votes"],
        reverse=True,
    )
    if len(ranked) < 2:
        raise RuntimeError(f"Expected at least two candidates for AC {constituency_no}")

    winner = ranked[0]
    runnerup = ranked[1]
    return {
        "winner_candidate": winner["candidate"],
        "winner_party_full": winner["party_full"],
        "winner_votes": winner["total_votes"],
        "winner_vote_share": winner["vote_share"],
        "runnerup_candidate": runnerup["candidate"],
        "runnerup_party_full": runnerup["party_full"],
        "runnerup_votes": runnerup["total_votes"],
        "runnerup_vote_share": runnerup["vote_share"],
        "margin": int(winner["total_votes"]) - int(runnerup["total_votes"]),
        "total_votes": total_votes,
        "source_url": url,
        "candidates": candidates,
    }


def find_wikipedia_constituency_table(markup: str) -> list[list[str]]:
    for table in parse_tables(markup):
        expanded = expand_rowspans(table)
        if any(row and row[0] == "#" and "Constituency" in row for row in expanded):
            data_rows = [row for row in expanded if row and row[0].isdigit()]
            if len(data_rows) >= 234:
                return data_rows
    raise RuntimeError("Could not find Wikipedia constituency mapping table")


def region_group(constituency_no: int, district: str) -> str:
    if district == "Chennai":
        return "Chennai Administrative District"
    if constituency_no in CHENNAI_URBAN_BELT_CONSTITUENCIES:
        return "Chennai Urban Belt"
    return ""


def parse_mapping() -> dict[int, dict[str, str]]:
    markup = fetch(WIKI_MAPPING_URL)
    rows = find_wikipedia_constituency_table(markup)
    mapping: dict[int, dict[str, str]] = {}
    for row in rows:
        constituency_no = int(row[0])
        reserved = row[2] if len(row) > 2 else "-"
        district = ADMIN_DISTRICT_OVERRIDES.get(constituency_no, row[5] if len(row) > 5 else "")
        reservation_type = "" if reserved in {"", "-"} else reserved
        mapping[constituency_no] = {
            "constituency_no": str(constituency_no),
            "constituency_name": row[1].upper(),
            "administrative_district": district,
            "region_group": region_group(constituency_no, district),
            "is_reserved": "true" if reservation_type else "false",
            "reservation_type": reservation_type,
            "notes": ADMIN_DISTRICT_OVERRIDE_NOTES.get(constituency_no, ""),
            "mapping_source_url": WIKI_MAPPING_URL,
            "mapping_verified_on": MAPPING_VERIFIED_ON,
        }
    return mapping


def write_mapping(mapping: dict[int, dict[str, str]]) -> None:
    columns = [
        "constituency_no",
        "constituency_name",
        "administrative_district",
        "region_group",
        "is_reserved",
        "reservation_type",
        "notes",
        "mapping_source_url",
        "mapping_verified_on",
    ]
    with MAPPING_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for constituency_no in sorted(mapping):
            writer.writerow(mapping[constituency_no])


def write_current_results(
    summaries: dict[int, dict[str, str]],
    mapping: dict[int, dict[str, str]],
    candidate_pages: dict[int, dict[str, object]],
    source_last_updated: str,
) -> None:
    columns = [
        "state",
        "year",
        "constituency_no",
        "constituency_name",
        "district",
        "region_group",
        "winner_candidate",
        "winner_party",
        "winner_votes",
        "winner_vote_share",
        "runnerup_candidate",
        "runnerup_party",
        "runnerup_votes",
        "runnerup_vote_share",
        "margin",
        "total_votes",
        "result_status",
        "source_url",
        "source_last_updated",
        "data_version",
    ]
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for constituency_no in sorted(summaries):
            candidate = candidate_pages[constituency_no]
            district_row = mapping[constituency_no]
            summary = summaries[constituency_no]
            writer.writerow(
                {
                    "state": STATE,
                    "year": YEAR,
                    "constituency_no": constituency_no,
                    "constituency_name": summary["constituency_name"],
                    "district": district_row["administrative_district"],
                    "region_group": district_row["region_group"],
                    "winner_candidate": candidate["winner_candidate"],
                    "winner_party": party_code(str(candidate["winner_party_full"])),
                    "winner_votes": candidate["winner_votes"],
                    "winner_vote_share": candidate["winner_vote_share"],
                    "runnerup_candidate": candidate["runnerup_candidate"],
                    "runnerup_party": party_code(str(candidate["runnerup_party_full"])),
                    "runnerup_votes": candidate["runnerup_votes"],
                    "runnerup_vote_share": candidate["runnerup_vote_share"],
                    "margin": candidate["margin"],
                    "total_votes": candidate["total_votes"],
                    "result_status": summary["result_status"],
                    "source_url": candidate["source_url"],
                    "source_last_updated": source_last_updated,
                    "data_version": DATA_VERSION,
                }
            )


def write_candidate_results(
    summaries: dict[int, dict[str, str]],
    mapping: dict[int, dict[str, str]],
    candidate_pages: dict[int, dict[str, object]],
    source_last_updated: str,
) -> None:
    columns = [
        "state",
        "year",
        "constituency_no",
        "constituency_name",
        "district",
        "candidate_rank",
        "candidate",
        "party",
        "party_full",
        "evm_votes",
        "postal_votes",
        "total_votes",
        "vote_share",
        "source_url",
        "source_last_updated",
        "data_version",
    ]
    with CANDIDATES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for constituency_no in sorted(summaries):
            district_row = mapping[constituency_no]
            summary = summaries[constituency_no]
            candidate_page = candidate_pages[constituency_no]
            ranked = sorted(
                candidate_page["candidates"],
                key=lambda item: int(item["total_votes"]),
                reverse=True,
            )
            for rank, candidate in enumerate(ranked, start=1):
                writer.writerow(
                    {
                        "state": STATE,
                        "year": YEAR,
                        "constituency_no": constituency_no,
                        "constituency_name": summary["constituency_name"],
                        "district": district_row["administrative_district"],
                        "candidate_rank": rank,
                        "candidate": candidate["candidate"],
                        "party": candidate["party"],
                        "party_full": candidate["party_full"],
                        "evm_votes": candidate["evm_votes"],
                        "postal_votes": candidate["postal_votes"],
                        "total_votes": candidate["total_votes"],
                        "vote_share": candidate["vote_share"],
                        "source_url": candidate_page["source_url"],
                        "source_last_updated": source_last_updated,
                        "data_version": DATA_VERSION,
                    }
                )


def main() -> int:
    DATA_DIR.mkdir(exist_ok=True)
    summaries, source_last_updated = parse_summary_pages()
    mapping = parse_mapping()
    if len(summaries) != 234:
        raise RuntimeError(f"Expected 234 ECI summaries, found {len(summaries)}")
    if len(mapping) != 234:
        raise RuntimeError(f"Expected 234 mapping rows, found {len(mapping)}")

    candidate_pages = {
        constituency_no: parse_candidate_page(constituency_no)
        for constituency_no in sorted(summaries)
    }

    write_mapping(mapping)
    write_current_results(summaries, mapping, candidate_pages, source_last_updated)
    write_candidate_results(summaries, mapping, candidate_pages, source_last_updated)
    print(f"Wrote {MAPPING_CSV}")
    print(f"Wrote {RESULTS_CSV}")
    print(f"Wrote {CANDIDATES_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
