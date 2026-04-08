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

function aggregateSurplusDeficit(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    let solar = 0;
    let importFlow = 0;
    let exportFlow = 0;
    let unmetEvents = 0;
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

        solar += Number(row.solar_generation) || 0;
        importFlow += Number(row.grid_import) || 0;
        exportFlow += Number(row.grid_export) || 0;
        unmetEvents += row.unmet_load ? 1 : 0;
        hasAnyData = true;
    });

    const selfConsumedSolar = Math.max(0, solar - exportFlow);

    return {
        hasAnyData,
        data: [
            { label: "Self-consumed solar", value: selfConsumedSolar, color: "#1f7a4a" },
            { label: "Exported surplus", value: exportFlow, color: "#f59e0b" },
            { label: "Grid import", value: importFlow, color: "#2563eb" }
        ],
        unmetEvents
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderSurplusDeficit(rows, state) {
    const container = d3.select("#chart-area-surplus-deficit");
    if (container.empty()) {
        return;
    }

    const result = aggregateSurplusDeficit(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const segments = result.data;
    const total = d3.sum(segments, (d) => d.value) || 1;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 20, bottom: 55, left: 20 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const barY = height / 2 - 24;
    const barHeight = 48;

    const x = d3.scaleLinear()
        .domain([0, total])
        .range([0, width]);

    let cursor = 0;
    segments.forEach((segment) => {
        const segmentWidth = x(segment.value);

        g.append("rect")
            .attr("x", cursor)
            .attr("y", barY)
            .attr("width", segmentWidth)
            .attr("height", barHeight)
            .attr("rx", 10)
            .attr("fill", segment.color);

        if (segmentWidth > 90) {
            g.append("text")
                .attr("x", cursor + segmentWidth / 2)
                .attr("y", barY + barHeight / 2 + 5)
                .attr("text-anchor", "middle")
                .attr("font-size", 12)
                .attr("fill", "#ffffff")
                .text(`${segment.label}`);
        }

        cursor += segmentWidth;
    });

    const legend = g.append("g")
        .attr("transform", `translate(0, -4)`);

    segments.forEach((segment, index) => {
        const row = legend.append("g")
            .attr("transform", `translate(${index * 155}, 0)`);

        row.append("line")
            .attr("x1", 0)
            .attr("x2", 18)
            .attr("y1", 8)
            .attr("y2", 8)
            .attr("stroke", segment.color)
            .attr("stroke-width", 3);

        row.append("text")
            .attr("x", 24)
            .attr("y", 12)
            .attr("font-size", 12)
            .attr("fill", "#334155")
            .text(segment.label);
    });

    g.append("text")
        .attr("x", width / 2)
        .attr("y", barY + barHeight + 28)
        .attr("text-anchor", "middle")
        .attr("font-size", 13)
        .attr("fill", "#334155")
        .text(`Total tracked balance: ${d3.format(".1f")(total)} kWh`);

    g.append("text")
        .attr("x", width / 2)
        .attr("y", barY + barHeight + 48)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text(`Unmet load events: ${result.unmetEvents}`);
}
