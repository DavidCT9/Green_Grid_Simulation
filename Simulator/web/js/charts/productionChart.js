const d3 = window.d3;

function normalizeSelection(value) {
    
    console.log("Que rollo " +  value);
    if (!value || value.toLowerCase() === "all") {
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

function filterRows(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const filtered = rows.filter((row) => {
        const matchesType = !selectedType || row.household_type === selectedType;
        const matchesWealth = !selectedWealth || row.wealth_level === selectedWealth;
        return matchesType && matchesWealth;
    });

    const groupedByTimestamp = new Map();

    filtered.forEach((row) => {
        const timestamp = Number(row.timestamp);
        if (!Number.isFinite(timestamp) || timestamp < 0 || timestamp >= maxSteps) {
            return;
        }

        if (!groupedByTimestamp.has(timestamp)) {
            groupedByTimestamp.set(timestamp, {
                timestamp,
                solar: 0,
                load: 0,
                gridImport: 0,
                gridExport: 0
            });
        }

        const bucket = groupedByTimestamp.get(timestamp);
        bucket.solar += Number(row.solar_generation) || 0;
        bucket.load += Number(row.load_demand) || 0;
        bucket.gridImport += Number(row.grid_import) || 0;
        bucket.gridExport += Number(row.grid_export) || 0;
    });

    return Array.from(groupedByTimestamp.values()).sort((a, b) => a.timestamp - b.timestamp);
}

function renderEmptyChart(container, message) {
    container.selectAll("*").remove();
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderProductionChart(rows, state) {
    const container = d3.select("#chart-area-main");
    if (container.empty()) {
        console.error("No container");
        
        return;
    }

    const d3Local = d3;
    if (!d3Local) {
        console.warn("D3 is not available for production chart.");
        return;
    }

    const grouped = filterRows(rows, state);

    if (!grouped.length) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    container.selectAll("*").remove();

    const canvasWidth = 960;
    const canvasHeight = 420;
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

    const x = d3Local.scaleLinear()
        .domain(d3Local.extent(grouped, (d) => d.timestamp))
        .range([0, width]);

    const yMax = d3Local.max(grouped, (d) => Math.max(d.solar, d.load, d.gridImport, d.gridExport)) || 0;
    const y = d3Local.scaleLinear()
        .domain([0, yMax * 1.12])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3Local.axisBottom(x).ticks(Math.min(10, grouped.length)));

    g.append("g")
        .call(d3Local.axisLeft(y).ticks(6));

    g.append("g")
        .attr("class", "grid-lines")
        .call(
            d3Local.axisLeft(y)
                .ticks(6)
                .tickSize(-width)
                .tickFormat("")
        )
        .selectAll("line")
        .attr("stroke", "#e5e7eb")
        .attr("stroke-dasharray", "4,4");

    const lineSolar = d3Local.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.solar));

    const lineLoad = d3Local.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.load));

    const lineImport = d3Local.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.gridImport));

    const lineExport = d3Local.line()
        .x((d) => x(d.timestamp))
        .y((d) => y(d.gridExport));

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#16a34a")
        .attr("stroke-width", 2.5)
        .attr("d", lineSolar);

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#dc2626")
        .attr("stroke-width", 2.5)
        .attr("d", lineLoad);

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#2563eb")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "6,4")
        .attr("d", lineImport);

    g.append("path")
        .datum(grouped)
        .attr("fill", "none")
        .attr("stroke", "#f59e0b")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "6,4")
        .attr("d", lineExport);

    const legend = [
        { label: "Solar", color: "#16a34a" },
        { label: "Load", color: "#dc2626" },
        { label: "Grid import", color: "#2563eb" },
        { label: "Grid export", color: "#f59e0b" }
    ];

    const legendGroup = g.append("g")
        .attr("transform", `translate(10, -20)`);

    legend.forEach((item, index) => {
        const row = legendGroup.append("g")
            .attr("transform", `translate(${index * 120}, 0)`);

        row.append("line")
            .attr("x1", 0)
            .attr("x2", 20)
            .attr("y1", 8)
            .attr("y2", 8)
            .attr("stroke", item.color)
            .attr("stroke-width", 3);

        row.append("text")
            .attr("x", 26)
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
        .text(`Time steps shown: 0 to ${Math.min(rangeToMaxSteps(state.timeRange), grouped[grouped.length - 1].timestamp + 1) - 1}`);
    console.log("Production chart created");
}
