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

function aggregateWealthComparison(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const order = ["low", "middle", "high", "luxury"];
    const labels = {
        low: "Low",
        middle: "Middle",
        high: "High",
        luxury: "Luxury"
    };

    const houseTotals = new Map();

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

        const houseId = row.household_id;
        if (houseId == null) {
            return;
        }

        if (!houseTotals.has(houseId)) {
            houseTotals.set(houseId, {
                wealth_level: row.wealth_level,
                revenue: 0,
                cost: 0
            });
        }

        const bucket = houseTotals.get(houseId);
        bucket.revenue += Number(row.revenue_exported) || 0;
        bucket.cost += Number(row.cost_imported) || 0;
    });

    const grouped = new Map();
    order.forEach((wealth) => {
        grouped.set(wealth, {
            wealth,
            label: labels[wealth] || wealth,
            houses: 0,
            totalSavings: 0
        });
    });

    let hasAnyData = false;

    houseTotals.forEach((house) => {
        const wealth = house.wealth_level;
        if (!grouped.has(wealth)) {
            grouped.set(wealth, {
                wealth,
                label: labels[wealth] || wealth,
                houses: 0,
                totalSavings: 0
            });
        }

        const bucket = grouped.get(wealth);
        bucket.houses += 1;
        bucket.totalSavings += (house.revenue - house.cost);
        hasAnyData = true;
    });

    const data = Array.from(grouped.values()).map((d) => ({
        wealth: d.wealth,
        label: d.label,
        houses: d.houses,
        avgSavings: d.houses > 0 ? d.totalSavings / d.houses : 0
    }));

    return {
        hasAnyData,
        data
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderWealthComparison(rows, state) {
    const container = d3.select("#chart-area-wealth-comparison");
    if (container.empty()) {
        return;
    }

    const result = aggregateWealthComparison(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const grouped = result.data;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 24, bottom: 45, left: 105 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const xMin = d3.min(grouped, (d) => d.avgSavings) || 0;
    const xMax = d3.max(grouped, (d) => d.avgSavings) || 0;
    const x = d3.scaleLinear()
        .domain([Math.min(0, xMin) * 1.15, Math.max(0, xMax) * 1.15])
        .nice()
        .range([0, width]);

    const y = d3.scaleBand()
        .domain(grouped.map((d) => d.label))
        .range([0, height])
        .padding(0.22);

    g.append("g")
        .call(d3.axisLeft(y));

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format("$,.0f")));

    g.append("g")
        .attr("class", "grid-lines")
        .call(
            d3.axisBottom(x)
                .ticks(6)
                .tickSize(-height)
                .tickFormat("")
        )
        .attr("transform", `translate(0,${height})`)
        .selectAll("line")
        .attr("stroke", "#e5e7eb")
        .attr("stroke-dasharray", "4,4");

    g.append("line")
        .attr("x1", x(0))
        .attr("x2", x(0))
        .attr("y1", 0)
        .attr("y2", height)
        .attr("stroke", "#64748b")
        .attr("stroke-width", 1.5);

    g.selectAll(".wealth-bar")
        .data(grouped)
        .enter()
        .append("rect")
        .attr("class", "wealth-bar")
        .attr("x", (d) => Math.min(x(0), x(d.avgSavings)))
        .attr("y", (d) => y(d.label))
        .attr("width", (d) => Math.abs(x(d.avgSavings) - x(0)))
        .attr("height", y.bandwidth())
        .attr("rx", 8)
        .attr("fill", (d) => d.avgSavings >= 0 ? "#1f7a4a" : "#dc2626");

    g.selectAll(".wealth-label")
        .data(grouped)
        .enter()
        .append("text")
        .attr("class", "wealth-label")
        .attr("x", (d) => d.avgSavings >= 0 ? x(d.avgSavings) + 8 : x(d.avgSavings) - 8)
        .attr("y", (d) => y(d.label) + y.bandwidth() / 2 + 4)
        .attr("text-anchor", (d) => d.avgSavings >= 0 ? "start" : "end")
        .attr("font-size", 12)
        .attr("fill", "#334155")
        .text((d) => d3.format("$,.0f")(d.avgSavings));

    const legend = [
        { label: "Positive savings", color: "#1f7a4a" },
        { label: "Negative savings", color: "#dc2626" }
    ];

    const legendGroup = g.append("g")
        .attr("transform", `translate(0, -8)`);

    legend.forEach((item, index) => {
        const row = legendGroup.append("g")
            .attr("transform", `translate(${index * 140}, -20)`);

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
        .attr("y", height + 34)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("Average net savings per household");
}
