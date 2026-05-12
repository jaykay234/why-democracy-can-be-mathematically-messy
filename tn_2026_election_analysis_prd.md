# PRD: Tamil Nadu 2026 Election Analysis Lab

## 1. Product name

**TN 2026 Election Analysis Lab**

A lightweight, Gist-friendly election analysis project with simple datasets, notebooks, and rich D3-style visuals to analyze the Tamil Nadu 2026 Assembly election and explore a fun district-based electoral-college hypothesis.

---

## 2. Executive intent

The 2026 Tamil Nadu Assembly election creates a powerful analytical story:

- A new party, TVK, emerges as the largest party.
- TVK wins **108 / 234 seats**, short of the **118 majority mark**.
- The Assembly is hung under the real constituency-based system.
- A hypothetical district-level electoral-college model may convert the same constituency results into a working majority.
- The deeper message: **electoral systems reward not just votes, but the geography and concentration of those votes.**

This project should make that story testable, visual, and easy to extend.

---

## 3. Core question

> How did the same political outcome produce a hung Assembly under the actual system, and how would the result change under alternative aggregation rules such as district-level electoral-college logic?

The project should help answer:

1. How did TVK, DMK, AIADMK, and others perform by constituency?
2. Where were the closest races?
3. Where were party wins geographically concentrated?
4. Which districts amplified TVK’s result?
5. How does district winner-take-all change the majority picture?
6. How do 2026 patterns compare with historical election wins?
7. What can parties learn if a re-election or future election happens?

---

## 4. Important disclaimer

This is a **data-analysis and visualization thought experiment**.

The district-based electoral-college model is **not** the actual Indian constitutional or electoral system. It is only a fun analytical lens to understand geographic efficiency and vote/seat concentration.

---

## 5. Target users

### Primary user

A political-data enthusiast or analyst who wants to understand the 2026 Tamil Nadu election through simple data and visuals.

### Secondary users

- Journalists and bloggers
- Students of political science
- Data visualization learners
- Engineers using Codex to build data apps
- Election observers interested in first-past-the-post distortions

---

## 6. MVP scope

### In scope

1. Simple CSV/JSON datasets
2. Python notebooks for analysis
3. D3 or Observable-style visual components
4. District-based electoral-college scenario engine
5. Historical comparison for previous Tamil Nadu elections
6. Gist-friendly documentation
7. Exportable visuals for LinkedIn/social posts

### Out of scope for MVP

1. Real-time election updates
2. Campaign finance analysis
3. Booth-level or polling-station-level analysis
4. Voter demographic inference
5. Predictive modeling for actual future election outcomes
6. Official claim that the hypothetical electoral-college model is legally valid

---

## 7. Source-of-truth strategy

### 7.1 Current 2026 election results

Use the official Election Commission of India results page as the primary source for:

- Constituency name
- Constituency number
- Winning candidate
- Winning party
- Runner-up candidate
- Runner-up party
- Margin
- Result status
- Party-wise seats
- Party-wise vote share when available

### 7.2 Data-refresh guardrail

The official result site may display provisional/public result data first and later publish final Form-20 data. Therefore:

- Store `source_url` and `source_last_updated` in every dataset.
- Add `data_version` to every generated file.
- Add a notebook section called **Reconciliation with Form-20**.
- Treat 2026 data as `official_public_result_snapshot` until final Form-20 data is ingested.

### 7.3 District boundary mapping

For the fun electoral-college model, district boundaries matter. The project must distinguish between:

- **Administrative district boundary**
- **Greater metro / political region grouping**
- **Custom analytical region**

Example correction:

- Chennai administrative district should be treated as **16 constituencies**, not 22.
- The broader Chennai urban belt may include Chennai + parts of Thiruvallur + Chengalpattu + Kancheepuram, but that must be labeled separately.

### 7.4 Historical election data

include historical seat winners from:

- 1967 onward for long-term Dravidian-era analysis
- Party lineage normalization, including party splits, alliances, and renames

---

## 8. Repository / Gist structure

Because this will be Gist-postable, keep it intentionally small.

```text
tn-2026-election-analysis/
  README.md
  PRD.md
  data/
    current_results_clean.csv
    district_constituency_mapping.csv
    historical_election_summary.csv
  notebooks/
    tn_2026_election_analysis.ipynb
  visuals/
    index.html
    styles.css
    app.js
  outputs/
    charts/
    social/
  docs/
    methodology.md
    data_dictionary.md
```

Design principle:

> Keep the source data thin and canonical. Build party summaries, district summaries, close-race tables, electoral-college outputs, and visual-ready JSON/CSV files through notebook code.

---

## 9. Dataset design

The MVP should avoid redundant derived datasets. The only required election-result source table is `current_results_clean.csv`. Every other 2026 output should be computed in the notebook.

### 9.1 Required dataset: `current_results_clean.csv`

One row per Assembly constituency.

```csv
state,year,constituency_no,constituency_name,district,region_group,winner_candidate,winner_party,winner_votes,winner_vote_share,runnerup_candidate,runnerup_party,runnerup_votes,runnerup_vote_share,margin,total_votes,result_status,source_url,data_version
Tamil Nadu,2026,21,Anna Nagar,Chennai,Chennai Administrative District,V.K. Ramkumar,TVK,,,,DMK,,21363,,Result Declared,https://results.eci.gov.in/ResultAcGenMay2026/statewiseS221.htm,official_public_snapshot_2026_05_05
Tamil Nadu,2026,8,Ambattur,Thiruvallur,Chennai Urban Belt,Balamurugan G,TVK,,,,DMK,,58781,,Result Declared,https://results.eci.gov.in/ResultAcGenMay2026/statewiseS221.htm,official_public_snapshot_2026_05_05
```

Notes:

- `district` should use administrative district.
- `region_group` can support analytical groupings like “Chennai Urban Belt.”
- Missing vote fields are allowed in early MVP if the public page parse does not expose all fields cleanly.
- Later Form-20 ingestion should fill candidate-level vote totals.
- `winner_party`, `district`, and `margin` are the minimum fields needed to power the first version.

Derived in notebook, not stored as primary source files:

- Party summary
- Party vote/seat share table
- District summary
- Close-race table
- Electoral-college scenario result
- Social-card-ready summary data

---

### 9.2 Required dataset: `district_constituency_mapping.csv`

One row per constituency.

```csv
constituency_no,constituency_name,administrative_district,region_group,is_reserved,reservation_type,notes
7,Maduravoyal,Chennai,Chennai Urban Belt,false,,Validate district assignment before scenario run
8,Ambattur,Thiruvallur,Chennai Urban Belt,false,,Part of wider Chennai urban belt but not Chennai administrative district
21,Anna Nagar,Chennai,Chennai Administrative District,false,,
```

Guardrail:

- Add a validation section in the notebook to confirm that each constituency maps to one administrative district.
- Example: Chennai administrative district should not be shown as 22 constituencies if strict administrative district logic is used.
- If the project uses a wider “Chennai Urban Belt,” it must be explicitly modeled as `region_group`, not as Chennai district.

---

### 9.3 Optional context dataset: `historical_election_summary.csv`

This should be a simple summary dataset, not a full constituency-level historical dataset for MVP.

Purpose:

- Paint the long historical picture.
- Show the dominance and rotation of major parties over time.
- Avoid spending MVP effort normalizing every constituency-level historical result from 2011 onward.

Recommended grain: one row per election year and party/alliance.

```csv
year,party_or_alliance,seats_won,vote_share,government_formed,chief_minister_or_leader,notes,source_url
1967,DMK-led,,,,First major Dravidian-era rupture,,
1977,AIADMK-led,,,,AIADMK era begins,,
2021,DMK-led,,,,Baseline before 2026,,
2026,TVK,108,34.92,false,Largest party but no sole majority,Official public result snapshot,
```

This dataset is intentionally high-level. It is enough to support a historical story card such as:

> “Tamil Nadu politics has historically moved through major party eras. The 2026 result can be analyzed as a possible new rupture, but the constituency-level proof comes from the current 2026 dataset.”

If later needed, the project can add a full `historical_constituency_results.csv`, but that should be a Phase 2 enhancement, not MVP.

---

## 10. Scenario rules

### 10.1 Actual Assembly system

Each constituency elects one MLA. Majority requires 118 MLAs out of 234.

Output:

```text
TVK = 108 / 234
Majority mark = 118
Outcome = Largest party, no sole majority
```

---

### 10.2 Hypothetical district electoral-college model

Rule:

> Each administrative district acts as a higher boundary. Each Assembly constituency equals one electoral vote. The party or bloc that wins the most constituencies in a district receives that district’s electoral votes. If the district is tied, electoral votes are split by actual MLA count.

Output:

```text
TVK hypothetical electoral votes = computed by scenario engine
Majority mark = 118
Outcome = majority or no majority
```

Important:

- The scenario engine must support multiple tie rules.
- The result should not be hard-coded.
- The district mapping must be validated before generating the final chart.

---

### 10.3 Alternative scenario modes

Support these modes in `scenario_config.yaml`:

```yaml
scenario_name: district_electoral_college
boundary_type: administrative_district
vote_unit: assembly_constituency
allocation_rule: winner_take_all_by_district
party_mode: party
majority_mark: 118
tie_rule: split_by_mla_count
include_region_grouping: false
```

Alternative values:

```yaml
allocation_rule:
  - winner_take_all_by_district

tie_rule:
  - split_by_mla_count

party_mode:
  - alliance_group
```

---

## 11. Single notebook requirements

Use one notebook only:

```text
notebooks/tn_2026_election_analysis.ipynb
```

The notebook should be readable as a full analytical story, not just a technical pipeline.

### Notebook sections

#### Section 1: Load data and assumptions

Goal:

- Load `current_results_clean.csv`.
- Load `district_constituency_mapping.csv`.
- Optionally load `historical_election_summary.csv`.
- Define constants such as total seats and majority mark.

Key checks:

```python
TOTAL_SEATS = 234
MAJORITY_MARK = 118
assert current_results["constituency_no"].nunique() == TOTAL_SEATS
```

---

#### Section 2: Clean and validate current election data

Goal:

- Normalize party names.
- Validate constituency count.
- Validate result status.
- Attach district mapping.
- Identify missing data fields.

Required output:

- Cleaned dataframe used for all downstream analysis.

---

#### Section 3: Build actual result summary from `current_results_clean.csv`

Goal:

- Compute party seat summary from the constituency-level result.
- Compute seat share.
- Add vote share only if available from source fields or a small manual reference table.
- Show majority gap.

Important:

- Do **not** maintain a separate `party_summary_2026.csv` as a source dataset.
- Party summary must be generated by grouping `current_results_clean.csv`.

Example:

```python
party_summary = (
    current_results
    .groupby("winner_party")
    .size()
    .reset_index(name="seats_won")
    .sort_values("seats_won", ascending=False)
)
party_summary["seat_share"] = party_summary["seats_won"] / TOTAL_SEATS
party_summary["majority_gap"] = party_summary["seats_won"] - MAJORITY_MARK
```

---

#### Section 4: District boundary validation

Goal:

- Validate constituency-to-district mapping.
- Catch errors like Chennai being treated as 22 instead of 16.
- Compare administrative district vs metro/region grouping.

Checks:

```python
district_counts = current_results.groupby("district")["constituency_no"].nunique()
assert district_counts.loc["Chennai"] == 16
```

Outputs:

- District constituency count table
- Mismatch warnings
- Region-group explanation table

---

#### Section 5: District and concentration analysis

Goal:

- Build district summary from current election data.
- Compute seats won by party in each district.
- Identify high-seat districts.
- Identify where TVK was geographically efficient.

Derived output:

```python
district_summary = current_results.pivot_table(
    index="district",
    columns="winner_party",
    values="constituency_no",
    aggfunc="count",
    fill_value=0
)
```

---

#### Section 6: Hypothetical electoral-college scenario

Goal:

- Apply district winner-take-all logic.
- Support tie rules.
- Compare real result vs hypothetical result.

Core function:

```python
def allocate_district_electoral_votes(district_df, party_col="winner_party", tie_rule="split_by_mla_count"):
    total_votes = len(district_df)
    party_counts = district_df[party_col].value_counts()
    max_count = party_counts.max()
    winners = party_counts[party_counts == max_count]

    if len(winners) == 1:
        return {winners.index[0]: total_votes}

    if tie_rule == "split_by_mla_count":
        return party_counts.to_dict()

    raise ValueError(f"Unsupported tie rule: {tie_rule}")
```

Outputs:

- Scenario table by district
- TVK hypothetical electoral vote total
- Majority gap
- Districts that amplify or penalize TVK

---

#### Section 7: Historical summary context

Goal:

- Use `historical_election_summary.csv` to paint the long arc.
- Keep this high-level for MVP.
- Avoid full constituency-level historical modeling unless added later.

Charts:

- Historical seat summary by election year
- Party/alliance era timeline
- 2026 disruption marker

---

#### Section 8: Visual exports

Goal:

- Generate chart-ready JSON/CSV in memory or under `outputs/`.
- Produce social-card screenshots or PNGs where practical.

Exports:

```text
outputs/charts/actual_party_summary.csv
outputs/charts/district_summary.csv
outputs/charts/electoral_college_result.csv
outputs/social/01_real_outcome.png
outputs/social/02_electoral_college_hypothesis.png
outputs/social/03_geographic_efficiency.png
outputs/social/04_historical_context.png
```

Important:

- These are outputs, not source datasets.
- They can be regenerated from the notebook at any time.

---

## 12. Visual requirements

### 12.1 Visual 1: Real outcome majority bar

Purpose:

Show TVK as largest party but short of majority.

Elements:

- Total seats: 234
- Majority mark: 118
- TVK: 108
- Gap: -10
- TVK vote share: 34.92%

Message:

> Largest party is not the same as majority party.

---

### 12.2 Visual 2: District electoral-college hypothesis

Purpose:

Show how district aggregation changes the result.

Elements:

- Real result: 108 / 234
- Hypothetical result: computed scenario result
- Majority mark: 118
- Tie-rule note

Message:

> The same constituency results can produce a different governing story under a different aggregation rule.

---

### 12.3 Visual 3: Geographic efficiency map

Purpose:

Explain concentration.

Elements:

- District-level summary
- Party winner by district
- District size by number of constituencies
- Highlight high-seat districts

Message:

> Concentration across high-value districts can matter as much as statewide vote share.

---

### 12.4 Visual 4: High-seat district amplifier chart

Purpose:

Show which districts carry more electoral weight in the hypothetical model.

Example bars:

```text
Chennai                 16
Coimbatore              10
Madurai                 10
Thiruvallur             10
Tiruchirapalli           9
Erode                    8
Tiruppur                 8
Chengalpattu             7
Namakkal                 6
```

Important:

- Do not label Chennai as 22 if using strict administrative district logic.
- Use “Chennai Urban Belt” only when intentionally grouping Chennai + surrounding urban districts.

---

### 12.5 Visual 5: Historical party-era summary

Purpose:

Paint the broad political history without requiring full constituency-level historical data in MVP.

Elements:

- Election year
- Leading party/alliance
- Seats won
- Government formed
- Major era marker
- 2026 disruption marker

Message:

> The historical picture should frame 2026 as a possible new rupture, while the detailed constituency-level proof remains focused on the current election dataset.

---

### 12.6 Visual 6: Close races and re-election sensitivity

Purpose:

Show whether a small swing could change government arithmetic.

Elements:

- X-axis: margin
- Y-axis: constituency or district
- Color: winning party
- Highlight constituencies with margin below 2,000 / 5,000 / 10,000

Message:

> In a hung or near-majority Assembly, a small number of close races can change the governing path.

---

## 13. D3 / frontend requirements

### 13.1 App shell

Single-page static app that can run from Gist/GitHub Pages/local server.

```text
visuals/index.html
visuals/styles.css
visuals/src/*.js
```

### 13.2 Controls

User should be able to change:

- Party vs alliance mode
- Administrative district vs region grouping
- Tie rule
- Margin threshold

Historical controls should be simple in MVP because the historical dataset is summary-level, not constituency-level.

### 13.3 Components

#### `seat-bar.js`

Reusable seat bar with majority threshold.

Inputs:

```js
{
  totalSeats: 234,
  majorityMark: 118,
  value: 108,
  label: "TVK seats"
}
```

#### `electoral-college-scenario.js`

Computes and renders hypothetical outcome.

Inputs:

```js
{
  districtSummary: [],
  allocationRule: "winner_take_all_by_district",
  tieRule: "split_by_mla_count",
  partyMode: "party"
}
```

#### `district-map.js`

MVP:

- Use a grid or tile map first.
- Full geographic map is optional.

Why:

- A tile map avoids boundary-shape complexity and keeps the Gist simple.

#### `historical-summary.js`

Renders high-level historical seat and government-formation context.

#### `close-race-scatter.js`

Renders margin sensitivity view.

---

## 14. Analytical metrics

### 14.1 Seat share

```text
seat_share = seats_won / 234
```

### 14.2 Vote-seat efficiency

```text
seat_efficiency = seat_share - vote_share
```

Purpose:

Shows whether a party converted votes into seats efficiently.

---

### 14.3 Majority gap

```text
majority_gap = seats_or_electoral_votes - 118
```

Interpretation:

- Negative = short of majority
- Positive = above majority

---

### 14.4 District dominance score

```text
district_dominance = party_seats_in_district / total_constituencies_in_district
```

Purpose:

Shows whether a party controls a district strongly or narrowly.

---

### 14.5 Geographic efficiency score

```text
geographic_efficiency = hypothetical_electoral_votes / actual_seats
```

Interpretation:

- Greater than 1 means the district model amplifies the party.
- Less than 1 means the district model penalizes the party.

---

### 14.6 Historical disruption marker

MVP version:

```text
historical_disruption_marker = narrative label based on historical_election_summary.csv
```

Purpose:

Frames whether 2026 looks like a major political rupture in the long arc of Tamil Nadu elections.

Future Phase 2 version:

```text
flip_intensity = number_of_constituencies_changed_party_since_previous_election / total_constituencies
```

This requires full historical constituency-level data and should not be part of the MVP unless that dataset is added later.

---

## 15. Storyboard for the public post

### Post title

**Tamil Nadu 2026: What if districts acted like an electoral college?**

### Story arc

1. Real result: TVK wins 108, short of 118.
2. The Assembly is hung under the actual system.
3. Fun hypothesis: district-level winner-take-all.
4. Same result can become majority depending on district concentration.
5. The deeper point is not party cheerleading; it is electoral math.
6. Votes matter, but **where** votes convert into seats also matters.

### Suggested LinkedIn caption

```text
A fun election-data thought experiment from Tamil Nadu 2026:

TVK won 108 of 234 seats — the largest party, but 10 short of the majority mark.

But what if each district acted like a higher boundary, and each Assembly constituency counted as an electoral vote?

That hypothetical model shifts the conversation from raw vote share to geographic efficiency.

The lesson is not that this should be the system. It should not be confused with India’s actual constitutional process.

The lesson is analytical:

When political support is concentrated across high-value districts, the same election can tell a very different story.

In first-past-the-post systems, votes do not only need to exist.
They need to land in the right places.
```

---

## 16. Build plan for Codex

### Phase 1: Minimal data and notebook skeleton

Tasks:

1. Create the simplified repo structure.
2. Add `current_results_clean.csv`.
3. Add `district_constituency_mapping.csv`.
4. Add optional `historical_election_summary.csv`.
5. Create one notebook: `tn_2026_election_analysis.ipynb`.
6. Add data dictionary and assumptions.

Acceptance criteria:

- Project runs with the canonical current result dataset.
- No separate party-summary source file is required.
- No multi-notebook pipeline is required for MVP.

---

### Phase 2: Actual election analysis in one notebook

Tasks:

1. Load `current_results_clean.csv`.
2. Generate party seat summary by grouping current results.
3. Generate close-race table.
4. Validate 234 constituencies.
5. Validate majority mark = 118.

Acceptance criteria:

- Notebook computes TVK 108 from the source rows.
- Seat bar renders TVK 108 vs majority 118.
- Party summary is derived, not stored as a source CSV.

---

### Phase 3: District boundary validation and concentration analysis

Tasks:

1. Join current results to district mapping.
2. Validate one constituency maps to one administrative district.
3. Generate district count table.
4. Flag unexpected district counts.
5. Build district concentration summary.

Acceptance criteria:

- Chennai administrative district count does not show as 22.
- Region grouping is separate from administrative district.
- High-seat district amplifier chart is generated from data.

---

### Phase 4: Electoral-college scenario engine

Tasks:

1. Build allocation logic inside the notebook.
2. Support tie rules.
3. Generate district-level output.
4. Compare real vs hypothetical outcome.

Acceptance criteria:

- Scenario output is computed, not hard-coded.
- Changing tie rule changes output as expected.
- Output includes majority gap.

---

### Phase 5: D3 visual app

Tasks:

1. Build static HTML shell.
2. Add seat bar visual.
3. Add district amplifier bar chart.
4. Add scenario comparison visual.
5. Add basic filters.

Acceptance criteria:

- App runs locally with `python -m http.server`.
- Visuals load from notebook-generated CSV/JSON outputs.
- Output is clean enough for screenshots.

---

### Phase 6: Historical summary visual

Tasks:

1. Load `historical_election_summary.csv`.
2. Render historical seat/government timeline.
3. Mark 2026 as a possible disruption point.

Acceptance criteria:

- The historical view paints the long arc without requiring full historical constituency-level data.
- Full constituency-level historical winners are explicitly deferred to Phase 2.

---

## 17. Codex prompt to start implementation

```text
Build a lightweight static data-analysis project from this PRD.

Create the simplified repo structure, minimal CSV datasets, one Python notebook, and a D3 visual shell.

Use only these source datasets for MVP:
1. data/current_results_clean.csv
2. data/district_constituency_mapping.csv
3. data/historical_election_summary.csv, optional and summary-level only

Do not create separate source CSV files for party summary, district summary, close races, or electoral-college results. Derive those inside the notebook from current_results_clean.csv and write them only as generated outputs if needed for visuals.

Prioritize:
1. canonical current-result data
2. district boundary validation
3. actual result vs hypothetical district electoral-college scenario
4. simple historical context
5. clean visuals that can be exported for a LinkedIn post

Do not hard-code final scenario result. Compute it from the constituency-level dataset and district mapping.

Use Python/pandas for the single notebook and vanilla D3 for frontend visuals.

Keep the project runnable from a GitHub Gist or simple static server.
```

---

## 18. Acceptance criteria summary

The MVP is successful when:

1. The project loads a single canonical 2026 constituency result dataset.
2. It confirms 234 constituencies and majority mark 118.
3. It derives party summary from `current_results_clean.csv`.
4. It shows TVK’s actual result as 108 / 234.
5. It validates administrative district boundaries.
6. It prevents Chennai administrative district from being misrepresented as 22 constituencies.
7. It computes district-level hypothetical electoral-college results from data.
8. It supports the `split_by_mla_count` tie rule.
9. It includes at least four polished visuals.
10. It includes simple historical context using summary-level historical data.
11. It uses one notebook, not a multi-notebook pipeline.
12. It is easy to paste into Gist and continue coding with Codex.

---

## 19. Risks and mitigations

| Risk                                               | Mitigation                                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------------------------- |
| ECI result page structure changes                  | Save raw snapshots and build parser tests                                          |
| Form-20 data differs from public snapshot          | Add reconciliation workflow                                                        |
| District mapping confusion                         | Separate administrative district from region group                                 |
| Hypothetical model is misunderstood as real system | Add clear disclaimer in README and visuals                                         |
| Party/alliance changes across years                | Keep historical dataset summary-level for MVP; defer full normalization to Phase 2 |
| D3 map complexity slows MVP                        | Start with tile/grid map instead of full GIS map                                   |

---

## 20. Final positioning

This project should not argue that Tamil Nadu should use an electoral college.

It should show something more interesting:

> A political result is not only shaped by voter preference. It is shaped by the counting system, the boundary system, and the geographic concentration of support.

That is the real analytical story.

