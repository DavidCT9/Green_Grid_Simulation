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

function aggregateHouseholdTypes(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const order = ["studio", "small_family", "large_family"];
    const labels = {
        studio: "Studio",
        small_family: "Small family",
        large_family: "Large family"
    };

    const grouped = new Map();

    order.forEach((type) => {
        grouped.set(type, {
            type,
            label: labels[type] || type,
            houses: new Set(),
            load: 0,
            importFlow: 0,
            exportFlow: 0
        });
    });

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

        const type = row.household_type;
        if (!grouped.has(type)) {
            grouped.set(type, {
                type,
                label: labels[type] || type,
                houses: new Set(),
                load: 0,
                importFlow: 0,
                exportFlow: 0
            });
        }

        const bucket = grouped.get(type);
        if (row.household_id != null) {
            bucket.houses.add(row.household_id);
        }
        bucket.load += Number(row.load_demand) || 0;
        bucket.importFlow += Number(row.grid_import) || 0;
        bucket.exportFlow += Number(row.grid_export) || 0;
        hasAnyData = true;
    });

    const output = Array.from(grouped.values()).map((d) => {
        const houseCount = Math.max(1, d.houses.size);
        return {
            type: d.type,
            label: d.label,
            houseCount: d.houses.size,
            avgLoad: d.load / houseCount,
            avgImport: d.importFlow / houseCount,
            avgExport: d.exportFlow / houseCount
        };
    });

    return {
        hasAnyData,
        data: output
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderHouseholdTypeComparison(rows, state) {
    const container = d3.select("#chart-area-household-type");
    if (container.empty()) {
        return;
    }

    const result = aggregateHouseholdTypes(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const grouped = result.data;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 20, bottom: 60, left: 65 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const metrics = [
        { key: "avgLoad", label: "Load", color: "#dc2626" },
        { key: "avgImport", label: "Grid import", color: "#2563eb" },
        { key: "avgExport", label: "Grid export", color: "#f59e0b" }
    ];

    const x0 = d3.scaleBand()
        .domain(grouped.map((d) => d.label))
        .range([0, width])
        .padding(0.24);

    const x1 = d3.scaleBand()
        .domain(metrics.map((d) => d.key))
        .range([0, x0.bandwidth()])
        .padding(0.14);

    const yMax = d3.max(grouped, (d) => Math.max(d.avgLoad, d.avgImport, d.avgExport)) || 1;
    const y = d3.scaleLinear()
        .domain([0, yMax * 1.15])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x0));

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

    const groups = g.selectAll(".bar-group")
        .data(grouped)
        .enter()
        .append("g")
        .attr("class", "bar-group")
        .attr("transform", (d) => `translate(${x0(d.label)},0)`);

    groups.selectAll("rect")
        .data((d) => metrics.map((metric) => ({
            metric: metric.key,
            label: metric.label,
            color: metric.color,
            value: d[metric.key]
        })))
        .enter()
        .append("rect")
        .attr("x", (d) => x1(d.metric))
        .attr("y", (d) => y(d.value))
        .attr("width", x1.bandwidth())
        .attr("height", (d) => height - y(d.value))
        .attr("rx", 6)
        .attr("fill", (d) => d.color);

    const legend = g.append("g")
        .attr("transform", `translate(0, -8)`);

    metrics.forEach((metric, index) => {
        const row = legend.append("g")
            .attr("transform", `translate(${index * 120}, -20)`);

        row.append("line")
            .attr("x1", 0)
            .attr("x2", 18)
            .attr("y1", 8)
            .attr("y2", 8)
            .attr("stroke", metric.color)
            .attr("stroke-width", 3);

        row.append("text")
            .attr("x", 24)
            .attr("y", 12)
            .attr("font-size", 12)
            .attr("fill", "#334155")
            .text(metric.label);
    });

    g.append("text")
        .attr("x", width / 2)
        .attr("y", height + 44)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("Household type");

    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -48)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("Average kWh per household");
}
