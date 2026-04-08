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

function aggregateBatteryUtilization(rows, state) {
    const selectedType = normalizeSelection(state.houseType);
    const selectedWealth = normalizeSelection(state.wealthLevel);
    const maxSteps = rangeToMaxSteps(state.timeRange);

    const buckets = [
        { label: "0-20%", min: 0, max: 20, count: 0 },
        { label: "20-40%", min: 20, max: 40, count: 0 },
        { label: "40-60%", min: 40, max: 60, count: 0 },
        { label: "60-80%", min: 60, max: 80, count: 0 },
        { label: "80-100%", min: 80, max: 101, count: 0 }
    ];

    let total = 0;

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

        const soc = Number(row.battery_soc);
        if (!Number.isFinite(soc)) {
            return;
        }

        const bucket = buckets.find((item, index) => {
            if (index === buckets.length - 1) {
                return soc >= item.min && soc <= 100;
            }
            return soc >= item.min && soc < item.max;
        });

        if (bucket) {
            bucket.count += 1;
            total += 1;
        }
    });

    return {
        hasAnyData: total > 0,
        data: buckets.map((b) => ({
            label: b.label,
            count: b.count,
            percent: total > 0 ? (b.count / total) * 100 : 0
        }))
    };
}

function renderEmptyChart(container, message) {
    container.html("");
    container.append("div")
        .attr("class", "empty-chart-message")
        .text(message);
}

export function renderBatteryUtilization(rows, state) {
    const container = d3.select("#chart-area-battery-utilization");
    if (container.empty()) {
        return;
    }

    const result = aggregateBatteryUtilization(rows, state);

    if (!result.hasAnyData) {
        renderEmptyChart(container, "No data available for the selected filters.");
        return;
    }

    const grouped = result.data;

    container.html("");

    const containerNode = container.node();
    const canvasWidth = Math.max(560, containerNode?.clientWidth || 800);
    const canvasHeight = 360;
    const margin = { top: 30, right: 20, bottom: 55, left: 65 };
    const width = canvasWidth - margin.left - margin.right;
    const height = canvasHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("width", canvasWidth)
        .attr("height", canvasHeight)
        .attr("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(grouped.map((d) => d.label))
        .range([0, width])
        .padding(0.2);

    const y = d3.scaleLinear()
        .domain([0, 100])
        .nice()
        .range([height, 0]);

    g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));

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

    g.selectAll("rect")
        .data(grouped)
        .enter()
        .append("rect")
        .attr("x", (d) => x(d.label))
        .attr("y", (d) => y(d.percent))
        .attr("width", x.bandwidth())
        .attr("height", (d) => height - y(d.percent))
        .attr("rx", 8)
        .attr("fill", "#1f7a4a");

    g.selectAll(".bar-label")
        .data(grouped)
        .enter()
        .append("text")
        .attr("class", "bar-label")
        .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
        .attr("y", (d) => y(d.percent) - 8)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#334155")
        .text((d) => `${d3.format(".0f")(d.percent)}%`);

    g.append("text")
        .attr("x", width / 2)
        .attr("y", height + 42)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#64748b")
        .text("State of charge bucket");
}
