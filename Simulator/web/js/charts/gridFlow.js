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

function aggregateGridFlow(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const filtered = rows.filter((row) => {
        const timestamp = Number(row.timestamp);
        if (!Number.isFinite(timestamp) || timestamp < 0 || timestamp >= maxSteps) {
            return false;
        }

        const matchesType = !selectedType || row.household_type === selectedType;
        const matchesWealth = !selectedWealth || row.wealth_level === selectedWealth;
        return matchesType && matchesWealth;
    });

    const byTimestamp = new Map();

    filtered.forEach((row) => {
        const timestamp = Number(row.timestamp);
        if (!Number.isFinite(timestamp)) {
            return;
        }

        if (!byTimestamp.has(timestamp)) {
            byTimestamp.set(timestamp, {
                timestamp,
                importFlow: 0,
                exportFlow: 0
            });
        }

        const bucket = byTimestamp.get(timestamp);
        bucket.importFlow += Number(row.grid_import) || 0;
        bucket.exportFlow += Number(row.grid_export) || 0;
    });

    return Array.from(byTimestamp.values()).sort((a, b) => a.timestamp - b.timestamp);
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderGridFlow(rows, state) {
    const container = d3.select("#chart-area-gridflow");

    console.log("que rollo que pex")
    console.log(container);
    if (container.empty()) {
        return;
    }
    console.log("que rollo que pex")

    const grouped = aggregateGridFlow(rows, state);

    if (!grouped.length) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(600, containerNode?.clientWidth || 900);
    const canvasHeight = 400;
    const margin = { top: 25, right: 20, bottom: 55, left: 65 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
        .domain(d3.extent(grouped, (d) => d.timestamp))
        .range([0, width])
        .nice();

    const maxFlow = d3.max(grouped, (d) => Math.max(d.importFlow, d.exportFlow)) || 1;
    const y = d3.scaleLinear()
        .domain([-maxFlow * 1.1, maxFlow * 1.1])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format("d")));

    g.append("g")
        .call(d3.axisLeft(y).ticks(6));

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

    const importLine = d3.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.importFlow));

    const exportLine = d3.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(-d.exportFlow));

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 3)
        .attr("d", importLine);

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#22c55e")
        .attr("stroke-width", 3)
        .attr("d", exportLine);

    const legend = [
        { label: "Import from grid", color: "#ef4444" },
        { label: "Export to grid", color: "#22c55e" },
        { label: "Zero line", color: "#64748b" }
    ];

    const legendGroup = g.append("g")
        .attr("transform", `translate(0, -5)`);

    legend.forEach((item, index) => {
        const row = legendGroup.append("g")
            .attr("transform", `translate(${index * 145}, 0)`);

        row.append("line")
            .attr("x1", 0)
            .attr("x2", 18)
            .attr("y1", 8)
            .attr("y2", 8)
            .attr("stroke", item.color)
            .attr("stroke-width", 3);

        row.append("text")
            .attr("x", 24)
            .attr("y", 12)
            .attr("font-size", 12)
            .attr("fill", "#334155")
            .text(item.label);
    });

    g.append("text")
        .attr("x", width / 2)
        .attr("y", height + 42)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("Time step");
}
