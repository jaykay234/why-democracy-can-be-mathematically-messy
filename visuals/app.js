const TOTAL_SEATS = 234;
const MAJORITY_MARK = 118;

const partyColors = new Map([
  ["TVK", "#0f8b6f"],
  ["DMK", "#c74444"],
  ["ADMK", "#2d6cdf"],
  ["INC", "#c4842b"],
  ["PMK", "#7b55c7"],
  ["IUML", "#9a6f22"],
  ["CPI", "#b33a3a"],
  ["CPI(M)", "#8e2b2b"],
  ["VCK", "#4b5f9f"],
  ["BJP", "#d97721"],
  ["DMDK", "#6c6f32"],
  ["AMMKMNKZ", "#8b5e7e"],
]);

function colorForParty(party) {
  return partyColors.get(party) || "#7c8582";
}

function colorForPole(label, index = 0) {
  const normalized = label.toUpperCase();
  if (normalized.includes("TVK")) return colorForParty("TVK");
  if (normalized.includes("DMK") && !normalized.includes("AIADMK")) return colorForParty("DMK");
  if (normalized.includes("AIADMK") || normalized.includes("ADMK")) return colorForParty("ADMK");
  if (normalized.includes("CONGRESS")) return colorForParty("INC");
  if (normalized.includes("CPI")) return colorForParty("CPI");
  if (normalized.includes("OTHER")) return colorForParty("Other");
  return ["#0f8b6f", "#c74444", "#2d6cdf", "#7c8582"][index] || "#7c8582";
}

function shortPoleLabel(label) {
  return label
    .replace("Indian National Congress", "Congress")
    .replace("Other parties/fronts", "Others")
    .replace("-led Alliance", "")
    .replace("-led Front", "")
    .replace("-led United Front", "")
    .replace("-Congress Alliance", "+Congress");
}

function countBy(rows, key) {
  return d3.rollup(
    rows,
    (items) => items.length,
    (row) => row[key],
  );
}

function allocateDistrict(rows) {
  const counts = countBy(rows, "winner_party");
  const maxSeats = d3.max(Array.from(counts.values()));
  const winners = Array.from(counts, ([party, seats]) => ({ party, seats })).filter(
    (item) => item.seats === maxSeats,
  );

  if (winners.length === 1) {
    return new Map([[winners[0].party, rows.length]]);
  }

  return counts;
}

function formatCounts(counts) {
  return Array.from(counts, ([party, seats]) => `${party}: ${seats}`).join(", ");
}

async function loadData() {
  if (window.TN_CURRENT_RESULTS && window.TN_CANDIDATE_RESULTS) {
    const rows = window.TN_CURRENT_RESULTS;
    const candidates = window.TN_CANDIDATE_RESULTS;
    const historical = window.TN_HISTORICAL_SUMMARY || [];
    normalizeData(rows, candidates, historical);
    return { rows, candidates, historical };
  }

  const rows = await d3.csv("../data/current_results_clean.csv", d3.autoType);
  const candidates = await d3.csv("../data/current_candidate_results.csv", d3.autoType);
  const historical = await d3.csv("../data/historical_election_summary.csv", d3.autoType);
  normalizeData(rows, candidates, historical);
  return { rows, candidates, historical };
}

function normalizeData(rows, candidates, historical = []) {
  rows.forEach((row) => {
    row.constituency_no = Number(row.constituency_no);
    row.margin = Number(row.margin);
    row.winner_votes = Number(row.winner_votes);
    row.runnerup_votes = Number(row.runnerup_votes);
    row.total_votes = Number(row.total_votes);
  });
  candidates.forEach((row) => {
    row.constituency_no = Number(row.constituency_no);
    row.candidate_rank = Number(row.candidate_rank);
    row.total_votes = Number(row.total_votes);
    row.vote_share = Number(row.vote_share);
  });
  historical.forEach((row) => {
    row.year = Number(row.year);
    row.total_seats = Number(row.total_seats);
    row.first_seats = Number(row.first_seats);
    row.second_seats = Number(row.second_seats);
    row.third_seats = Number(row.third_seats);
    row.other_seats = Number(row.other_seats);
  });
}

function buildScenario(rows) {
  const actualCounts = countBy(rows, "winner_party");
  const districts = d3.groups(rows, (row) => row.district).map(([district, districtRows]) => {
    const actual = countBy(districtRows, "winner_party");
    const allocation = allocateDistrict(districtRows);
    return {
      district,
      rows: districtRows,
      seats: districtRows.length,
      actual,
      allocation,
      leader: Array.from(actual, ([party, seats]) => ({ party, seats })).sort((a, b) => b.seats - a.seats)[0],
      tvkActual: actual.get("TVK") || 0,
      tvkAllocated: allocation.get("TVK") || 0,
      tie: allocation.size > 1,
    };
  });

  const scenarioTotals = new Map();
  districts.forEach((district) => {
    district.allocation.forEach((votes, party) => {
      scenarioTotals.set(party, (scenarioTotals.get(party) || 0) + votes);
    });
  });

  return { actualCounts, districts, scenarioTotals };
}

function renderMetrics(rows, scenario) {
  const actualTvk = scenario.actualCounts.get("TVK") || 0;
  const hypothesisTvk = scenario.scenarioTotals.get("TVK") || 0;
  const sourceLastUpdated = rows[0]?.source_last_updated || "Unknown snapshot";

  d3.select("#majority-party").text(`${actualTvk} (TVK)`);
  d3.select("#hypothesis-tvk").text(`${hypothesisTvk} (TVK)`);
  d3.select("#scenario-outcome").text(
    hypothesisTvk >= MAJORITY_MARK ? "TVK passing 118 need" : "TVK below 118 need",
  );
  d3.select("#snapshot-date").text(sourceLastUpdated);
}

function renderChoiceSchematic() {
  const panels = [
    {
      title: "Two serious choices",
      caption: "A majority winner is easier to explain.",
      values: [
        { label: "A", value: 54, color: "#0f8b6f" },
        { label: "B", value: 46, color: "#c74444" },
      ],
    },
    {
      title: "Three serious choices",
      caption: "A plurality winner can still be below 50%.",
      values: [
        { label: "A", value: 38, color: "#0f8b6f" },
        { label: "B", value: 34, color: "#c74444" },
        { label: "C", value: 28, color: "#2d6cdf" },
      ],
    },
  ];

  const container = d3.select("#choice-schematic");
  container.selectAll("*").remove();

  const width = container.node().clientWidth;
  const isNarrow = width < 560;
  const height = isNarrow ? 360 : Math.max(container.node().clientHeight, 260);
  const margin = { top: 24, right: 24, bottom: 24, left: 24 };
  const panelGap = 24;
  const panelWidth = isNarrow
    ? width - margin.left - margin.right
    : (width - margin.left - margin.right - panelGap) / 2;
  const barHeight = 34;
  const svg = container.append("svg").attr("width", width).attr("height", height);
  const x = d3.scaleLinear().domain([0, 100]).range([0, panelWidth]);

  panels.forEach((panel, panelIndex) => {
    const panelX = isNarrow ? margin.left : margin.left + panelIndex * (panelWidth + panelGap);
    const panelY = isNarrow ? margin.top + panelIndex * 160 : margin.top;
    const g = svg.append("g").attr("transform", `translate(${panelX},${panelY})`);

    g.append("text").attr("class", "mini-value-label").attr("x", 0).attr("y", 0).text(panel.title);
    g.append("text").attr("class", "mini-caption").attr("x", 0).attr("y", 20).text(panel.caption);

    g.append("line")
      .attr("class", "mini-majority-line")
      .attr("x1", x(50))
      .attr("x2", x(50))
      .attr("y1", 50)
      .attr("y2", 100);

    let cursor = 0;
    panel.values.forEach((item) => {
      const segmentWidth = x(item.value);
      g.append("rect")
        .attr("x", x(cursor))
        .attr("y", 58)
        .attr("width", segmentWidth)
        .attr("height", barHeight)
        .attr("fill", item.color);
      if (segmentWidth > 42) {
        g.append("text")
          .attr("class", "bar-label")
          .attr("x", x(cursor) + segmentWidth / 2)
          .attr("y", 80)
          .attr("text-anchor", "middle")
          .text(`${item.label} ${item.value}%`);
      }
      cursor += item.value;
    });

    g.append("text")
      .attr("class", "majority-label")
      .attr("x", x(50) + 6)
      .attr("y", 118)
      .text("50% majority");
  });
}

function renderHistoricalStats(historical) {
  const pre2026 = historical.filter((row) => row.year < 2026);
  const current = historical.find((row) => row.year === 2026);
  const topTwoShare = (row) => (row.first_seats + row.second_seats) / row.total_seats;
  const topThreeShare = (row) => (row.first_seats + row.second_seats + row.third_seats) / row.total_seats;
  const bipolarYears = pre2026.filter((row) => row.pattern.includes("bipolar")).length;
  const averageTopTwo = d3.mean(pre2026, topTwoShare);
  const currentTopThree = current ? topThreeShare(current) : 0;

  d3.select("#historical-stats")
    .html("")
    .selectAll("div")
    .data([
      { label: "Elections tracked", value: `${historical.length} contests` },
      { label: "Two-pole pattern", value: `${bipolarYears} of ${pre2026.length} before 2026` },
      { label: "Avg top-two seats", value: d3.format(".0%")(averageTopTwo) },
      { label: "2026 top-three seats", value: d3.format(".0%")(currentTopThree) },
    ])
    .join("div")
    .attr("class", "summary-row")
    .html(
      (row) => `
        <span>${row.label}</span>
        <strong>${row.value}</strong>
      `,
    );
}

function historicalSegments(row) {
  return [
    { label: row.first_pole, seats: row.first_seats, index: 0 },
    { label: row.second_pole, seats: row.second_seats, index: 1 },
    { label: row.third_pole, seats: row.third_seats, index: 2 },
    { label: "Others", seats: row.other_seats, index: 3 },
  ].filter((segment) => segment.seats > 0);
}

function renderHistoricalTimeline(historical) {
  const rows = historical.slice().sort((a, b) => d3.ascending(a.year, b.year));
  const container = d3.select("#historical-chart");
  container.selectAll("*").remove();
  if (!rows.length) return;

  const width = container.node().clientWidth;
  const rowHeight = width < 700 ? 34 : 38;
  const margin = { top: 26, right: 28, bottom: 42, left: 66 };
  const height = margin.top + margin.bottom + rows.length * rowHeight;
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = rows.length * rowHeight;

  const svg = container.append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const x = d3.scaleLinear().domain([0, TOTAL_SEATS]).range([0, innerWidth]);
  const y = d3.scaleBand()
    .domain(rows.map((row) => row.year))
    .range([0, innerHeight])
    .padding(0.2);

  g.append("g")
    .attr("class", "axis historical-axis")
    .call(d3.axisLeft(y).tickSize(0))
    .select(".domain")
    .remove();

  g.append("g")
    .attr("class", "axis")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x).tickValues([0, 59, 118, 177, 234]).tickSizeOuter(0));

  g.append("line")
    .attr("class", "majority-line")
    .attr("x1", x(MAJORITY_MARK))
    .attr("x2", x(MAJORITY_MARK))
    .attr("y1", -8)
    .attr("y2", innerHeight + 6);

  g.append("text")
    .attr("class", "majority-label")
    .attr("x", x(MAJORITY_MARK) + 6)
    .attr("y", -10)
    .text("118 majority");

  rows.forEach((row) => {
    let cursor = 0;
    const segments = historicalSegments(row);

    segments.forEach((segment) => {
      const start = cursor;
      cursor += segment.seats;
      const segmentWidth = x(segment.seats);
      const segmentX = x(start);

      g.append("rect")
        .attr("x", segmentX)
        .attr("y", y(row.year))
        .attr("width", Math.max(1, segmentWidth))
        .attr("height", y.bandwidth())
        .attr("fill", colorForPole(segment.label, segment.index))
        .on("mousemove", (event) => {
          showTooltip(
            event,
            String(row.year),
            `<div>${row.first_pole}: ${row.first_seats} seats</div>
             <div>${row.second_pole}: ${row.second_seats} seats</div>
             <div>${row.third_pole}: ${row.third_seats} seats</div>
             <div>Others: ${row.other_seats} seats</div>
             <div>${row.notes}</div>`,
          );
        })
        .on("mouseleave", hideTooltip);

      if (segmentWidth > 62) {
        g.append("text")
          .attr("class", "bar-label historical-segment-label")
          .attr("x", segmentX + segmentWidth / 2)
          .attr("y", y(row.year) + y.bandwidth() / 2 + 4)
          .attr("text-anchor", "middle")
          .text(`${shortPoleLabel(segment.label)} ${segment.seats}`);
      }
    });
  });
}

function renderHungSummary(scenario) {
  const actual = Array.from(scenario.actualCounts, ([party, seats]) => ({ party, seats }))
    .sort((a, b) => b.seats - a.seats);
  const topRows = actual.slice(0, 5);
  const largest = topRows[0];

  d3.select("#hung-summary")
    .html("")
    .selectAll("div")
    .data([
      { label: "Largest party", value: `${largest.seats} (${largest.party})` },
      { label: "Majority mark", value: MAJORITY_MARK },
      { label: "Majority gap", value: `${largest.seats - MAJORITY_MARK}` },
      { label: "Seat spread", value: topRows.map((row) => `${row.party} ${row.seats}`).join(" | ") },
    ])
    .join("div")
    .attr("class", "summary-row")
    .html(
      (row) => `
        <span>${row.label}</span>
        <strong>${row.value}</strong>
      `,
    );
}

function renderComparison(scenario) {
  const actual = Array.from(scenario.actualCounts, ([party, seats]) => ({
    mode: "Actual Assembly",
    party,
    seats,
  }));
  const hypothesis = Array.from(scenario.scenarioTotals, ([party, seats]) => ({
    mode: "District Hypothesis",
    party,
    seats,
  }));

  const modes = ["Actual Assembly", "District Hypothesis"];
  const dataByMode = new Map([
    ["Actual Assembly", actual.sort((a, b) => b.seats - a.seats)],
    ["District Hypothesis", hypothesis.sort((a, b) => b.seats - a.seats)],
  ]);

  const container = d3.select("#comparison-chart");
  container.selectAll("*").remove();

  const width = container.node().clientWidth;
  const height = Math.max(container.node().clientHeight, 280);
  const margin = { top: 30, right: 30, bottom: 42, left: 150 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const svg = container.append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear().domain([0, TOTAL_SEATS]).range([0, innerWidth]);
  const y = d3.scaleBand().domain(modes).range([0, innerHeight]).padding(0.36);

  g.append("g")
    .attr("class", "axis")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x).tickValues([0, 59, 118, 177, 234]).tickSizeOuter(0));

  g.append("g").attr("class", "axis").call(d3.axisLeft(y).tickSize(0));

  g.append("line")
    .attr("class", "majority-line")
    .attr("x1", x(MAJORITY_MARK))
    .attr("x2", x(MAJORITY_MARK))
    .attr("y1", -10)
    .attr("y2", innerHeight + 8);

  g.append("text")
    .attr("class", "majority-label")
    .attr("x", x(MAJORITY_MARK) + 6)
    .attr("y", -12)
    .text("118 majority");

  modes.forEach((mode) => {
    let cursor = 0;
    g.selectAll(`rect.${mode.replaceAll(" ", "-")}`)
      .data(dataByMode.get(mode))
      .join("rect")
      .attr("x", (d) => {
        const start = cursor;
        cursor += d.seats;
        return x(start);
      })
      .attr("y", y(mode))
      .attr("width", (d) => x(d.seats))
      .attr("height", y.bandwidth())
      .attr("fill", (d) => colorForParty(d.party))
      .on("mousemove", (event, d) => showTooltip(event, d.party, `${d.seats} seats or electoral votes`))
      .on("mouseleave", hideTooltip);

    cursor = 0;
    g.selectAll(`text.${mode.replaceAll(" ", "-")}`)
      .data(dataByMode.get(mode).filter((d) => d.seats >= 8))
      .join("text")
      .attr("class", "bar-label")
      .attr("x", (d) => {
        const preceding = dataByMode
          .get(mode)
          .slice(0, dataByMode.get(mode).indexOf(d))
          .reduce((sum, item) => sum + item.seats, 0);
        return x(preceding + d.seats / 2);
      })
      .attr("y", y(mode) + y.bandwidth() / 2 + 4)
      .attr("text-anchor", "middle")
      .text((d) => `${d.party} ${d.seats}`);
  });
}

function renderDistricts(scenario) {
  const districts = scenario.districts.sort((a, b) => {
    const tvkDiff = b.tvkAllocated - a.tvkAllocated;
    if (tvkDiff) return tvkDiff;
    return d3.ascending(a.district, b.district);
  });

  const container = d3.select("#district-chart");
  container.selectAll("*").remove();

  const width = container.node().clientWidth;
  const rowHeight = 28;
  const margin = { top: 28, right: 28, bottom: 28, left: 148 };
  const height = margin.top + margin.bottom + districts.length * rowHeight;
  const innerWidth = width - margin.left - margin.right;

  const svg = container.append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const x = d3.scaleLinear().domain([0, d3.max(districts, (d) => d.seats)]).range([0, innerWidth]);
  const y = d3.scaleBand()
    .domain(districts.map((d) => d.district))
    .range([0, districts.length * rowHeight])
    .padding(0.22);

  g.append("g")
    .attr("class", "axis")
    .call(d3.axisLeft(y).tickSize(0))
    .select(".domain")
    .remove();

  districts.forEach((district) => {
    const yPos = y(district.district);
    let cursor = 0;
    const segments = Array.from(district.allocation, ([party, votes]) => ({ party, votes })).sort(
      (a, b) => b.votes - a.votes,
    );

    g.selectAll(`rect-${district.district}`)
      .data(segments)
      .join("rect")
      .attr("x", (d) => {
        const start = cursor;
        cursor += d.votes;
        return x(start);
      })
      .attr("y", yPos)
      .attr("width", (d) => Math.max(1, x(d.votes)))
      .attr("height", y.bandwidth())
      .attr("fill", (d) => colorForParty(d.party))
      .on("mousemove", (event) => {
        showTooltip(
          event,
          district.district,
          `${district.seats} constituencies<br>Actual: ${formatCounts(district.actual)}<br>Allocated: ${formatCounts(district.allocation)}`,
        );
      })
      .on("mouseleave", hideTooltip);

    g.append("text")
      .attr("class", "vote-label")
      .attr("x", Math.min(x(district.seats) + 8, innerWidth - 44))
      .attr("y", yPos + y.bandwidth() / 2 + 4)
      .text(district.tie ? "split" : district.leader.party);
  });
}

function formatVotes(value) {
  return d3.format(",")(value);
}

function formatMarginPercent(row) {
  return d3.format(".2%")(row.margin / row.total_votes);
}

function candidateCell(candidate) {
  if (!candidate) {
    return `<div class="candidate-row candidate-row--empty"><span class="empty-rank">—</span></div>`;
  }
  return `
    <div class="candidate-row">
      <div class="party-line">
        <span class="party-dot" style="background:${colorForParty(candidate.party)}"></span>
        <strong>${candidate.party}</strong>
      </div>
      <div class="candidate-name">${candidate.candidate}</div>
      <div class="vote-total">${formatVotes(candidate.total_votes)} votes</div>
    </div>
  `;
}

function renderCloseRaces(rows, candidates) {
  const candidatesByConstituency = d3.group(candidates, (row) => row.constituency_no);
  const applyMarginFilter = d3.select("#margin-filter").property("checked");
  const filteredRows = applyMarginFilter
    ? rows.filter((row) => row.margin / row.total_votes < 0.01)
    : rows;
  const closeRows = filteredRows
    .slice()
    .sort((a, b) => a.margin - b.margin)
    .slice(0, applyMarginFilter ? filteredRows.length : 10);

  d3.select("#close-race-summary").text(
    applyMarginFilter
      ? `Showing all ${filteredRows.length} constituencies with winner margins under 1% of total votes.`
      : "Showing the 10 closest races by raw winner margin.",
  );

  const tbody = d3.select("#close-races");
  tbody
    .selectAll("tr")
    .data(closeRows)
    .join("tr")
    .html((row) => raceRowHtml(row, candidatesByConstituency));
}

function raceBreakdownCells(row, candidatesByConstituency) {
  const ranked = (candidatesByConstituency.get(row.constituency_no) || [])
    .slice()
    .sort((a, b) => b.total_votes - a.total_votes);
  const topThree = ranked.slice(0, 3);
  const others = ranked.slice(3);
  const othersVotes = d3.sum(others, (candidate) => candidate.total_votes);

  const rankCells = [0, 1, 2]
    .map((i) => `<td class="candidate-cell party-rank-cell">${candidateCell(topThree[i])}</td>`)
    .join("");

  return `
    ${rankCells}
    <td class="candidate-cell others-cell">
      <div class="party-line">
        <span class="party-dot other-dot"></span>
        <strong>Others</strong>
      </div>
      <div class="candidate-name">${others.length} candidates including NOTA</div>
      <div class="vote-total">${formatVotes(othersVotes)} votes</div>
    </td>
  `;
}

function raceRowHtml(row, candidatesByConstituency) {
  return `
    <td>${row.constituency_name}</td>
    <td class="margin-cell">
      <strong>${formatVotes(row.margin)}</strong>
      <em>${formatMarginPercent(row)} of total votes</em>
      <span>${row.winner_party} over ${row.runnerup_party}</span>
    </td>
    ${raceBreakdownCells(row, candidatesByConstituency)}
  `;
}

function renderStrongholds(rows, candidates) {
  const candidatesByConstituency = d3.group(candidates, (row) => row.constituency_no);
  const strongholds = rows
    .slice()
    .sort((a, b) => b.margin / b.total_votes - a.margin / a.total_votes)
    .slice(0, 15);

  d3.select("#stronghold-summary").text(
    `Top ${strongholds.length} constituencies by winner margin percentage.`,
  );

  d3.select("#strongholds")
    .selectAll("tr")
    .data(strongholds)
    .join("tr")
    .html((row) => raceRowHtml(row, candidatesByConstituency));
}

function showTooltip(event, title, body) {
  d3.select("#tooltip")
    .style("display", "block")
    .style("left", `${event.clientX + 14}px`)
    .style("top", `${event.clientY + 14}px`)
    .html(`<strong>${title}</strong>${body}`);
}

function hideTooltip() {
  d3.select("#tooltip").style("display", "none");
}

function render(rows, candidates, historical) {
  const scenario = buildScenario(rows);
  renderChoiceSchematic();
  renderHistoricalStats(historical);
  renderHistoricalTimeline(historical);
  renderMetrics(rows, scenario);
  renderHungSummary(scenario);
  renderComparison(scenario);
  renderDistricts(scenario);
  renderCloseRaces(rows, candidates);
  renderStrongholds(rows, candidates);
}

loadData().then(({ rows, candidates, historical }) => {
  render(rows, candidates, historical);
  window.addEventListener("resize", () => render(rows, candidates, historical));
  d3.select("#margin-filter").on("change", () => renderCloseRaces(rows, candidates));
});
