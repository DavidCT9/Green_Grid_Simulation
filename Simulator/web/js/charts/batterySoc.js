const d3 = window.d3;

function normalizeSelection(value) {
    if (!value || value === "all") {
        return null;
    }
    return String(value).toLowerCase();
}

function rangeToMaxSteps(range) {
    const stepsByRange = {
        day: 24,
        week: 24 * 7,
        month: 24 * 30,
        quarter: 24 * 90,
        year: 24 * 365
    };

    return stepsByRange[range] || stepsByRange.month;
}

function aggregateBatterySoc(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const byTimestamp = new Map();
    let hasAnyData = false;

    rows.forEach((row) => {
        const timestamp = Number(row.timestamp);
        if (!Number.isFinite(timestamp) || timestamp < 0 || timestamp >= maxSteps) {
            return;
        }

        const matchesType = !selectedType || row.household_type === selectedType;
        const matchesWealth = !selectedWealth || row.wealth_level === selectedWealth;
        if (!matchesType || !matchesWealth) {
            return;
        }

        if (!byTimestamp.has(timestamp)) {
            byTimestamp.set(timestamp, { timestamp, socSum: 0, count: 0 });
        }

        const bucket = byTimestamp.get(timestamp);
        bucket.socSum += Number(row.battery_soc) || 0;
        bucket.count += 1;
        hasAnyData = true;
    });

    return {
        hasAnyData,
        data: Array.from(byTimestamp.values())
            .sort((a, b) => a.timestamp - b.timestamp)
            .map((d) => ({
                timestamp: d.timestamp,
                avgSoc: d.count > 0 ? d.socSum / d.count : 0
            }))
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderBatterySoc(rows, state) {
    const container = d3.select("#chart-area-battery-soc");
    if (container.empty()) {
        return;
    }

    const result = aggregateBatterySoc(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const grouped = result.data;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 20, bottom: 50, left: 65 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const xExtent = d3.extent(grouped, (d) => d.timestamp);
    const xDomain = xExtent[0] === xExtent[1] ? [xExtent[0], xExtent[0] + 1] : xExtent;

    const x = d3.scaleLinear()
        .domain(xDomain)
        .range([0, width])
        .nice();

    const y = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format("d")));

    g.append("g")
        .call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d}%`));

    g.append("g")
        .attr("class", "grid-lines")
        .call(
            d3.axisLeft(y)
                .ticks(5)
                .tickSize(-width)
                .tickFormat("")
        )
        .selectAll("line")
        .attr("stroke", "#e5e7eb")
        .attr("stroke-dasharray", "4,4");

    g.append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", y(20))
        .attr("y2", y(20))
        .attr("stroke", "#cbd5e1")
        .attr("stroke-dasharray", "5,4");

    g.append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", y(80))
        .attr("y2", y(80))
        .attr("stroke", "#cbd5e1")
        .attr("stroke-dasharray", "5,4");

    g.append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", y(0))
        .attr("y2", y(0))
        .attr("stroke", "#64748b")
        .attr("stroke-width", 1.5);

    const area = d3.area()
        .x((d) => x(d.timestamp))
        .y0(y(0))
        .y1((d) => y(d.avgSoc));

    const line = d3.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.avgSoc));

    g.append("path")
        .datum(grouped)
        .attr("fill", "rgba(31, 122, 74, 0.18)")
        .attr("d", area);

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#1f7a4a")
        .attr("stroke-width", 2.5)
        .attr("d", line);

    g.append("text")
        .attr("x", width / 2)
        .attr("y", height + 36)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("Time step");
}
