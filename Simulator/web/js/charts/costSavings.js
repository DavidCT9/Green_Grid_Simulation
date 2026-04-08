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

function aggregateCostSavings(rows, state) {
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
            byTimestamp.set(timestamp, { timestamp, revenue: 0, cost: 0 });
        }

        const bucket = byTimestamp.get(timestamp);
        bucket.revenue += Number(row.revenue_exported) || 0;
        bucket.cost += Number(row.cost_imported) || 0;
        hasAnyData = true;
    });

    const points = Array.from(byTimestamp.values())
        .sort((a, b) => a.timestamp - b.timestamp)
        .map((d) => ({
            timestamp: d.timestamp,
            net: d.revenue - d.cost
        }));

    let cumulative = 0;
    const cumulativePoints = points.map((d) => {
        cumulative += d.net;
        return {
            timestamp: d.timestamp,
            cumulative
        };
    });

    return {
        hasAnyData,
        data: cumulativePoints
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderCostSavings(rows, state) {
    const container = d3.select("#chart-area-cost-savings");
    if (container.empty()) {
        return;
    }

    const result = aggregateCostSavings(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const grouped = result.data;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 20, bottom: 50, left: 80 };
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

    const yMin = d3.min(grouped, (d) => d.cumulative) || 0;
    const yMax = d3.max(grouped, (d) => d.cumulative) || 0;
    const y = d3.scaleLinear()
        .domain([Math.min(0, yMin) * 1.1, Math.max(0, yMax) * 1.1])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format("d")));

    g.append("g")
        .call(d3.axisLeft(y).ticks(6).tickFormat(d3.format("$,.0f")));

    g.append("g")
        .attr("class", "grid-lines")
        .call(
            d3.axisLeft(y)
                .ticks(6)
                .tickSize(-width)
                .tickFormat("")
        )
        .selectAll("line")
        .attr("stroke", "#e5e7eb")
        .attr("stroke-dasharray", "4,4");

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
        .y1((d) => y(d.cumulative));

    const line = d3.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.cumulative));

    g.append("path")
        .datum(grouped)
        .attr("fill", "rgba(31, 122, 74, 0.16)")
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
