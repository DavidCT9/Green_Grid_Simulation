/*
 * main.js
 */

document.addEventListener("DOMContentLoaded", () => {
    const controls = {
        timeRange: document.getElementById("timeRange"),
        houseType: document.getElementById("houseType"),
        wealthLevel: document.getElementById("wealthLevel"),
        metricView: document.getElementById("metricView")
    };

    Object.entries(controls).forEach(([name, control]) => {
        if (!control) return;
        control.addEventListener("change", () => {
            console.log(`${name} changed to`, control.value);
        });
    });

    loadAggregatedSummary();
});

async function loadAggregatedSummary() {
    const sources = [
        "/data/summary/aggregated_data.json"
    ];

    let summary = null;
    let loadedFrom = null;

    for (const source of sources) {
        try {
            const response = await fetch(source, { cache: "no-store" });
            if (!response.ok) continue;
            summary = await response.json();
            loadedFrom = source;
            break;
        } catch (error) {
            // Try the next candidate path.
        }
    }

    if (!summary) {
        console.warn("Could not load aggregated data from any known path.");
        renderKpis(null, null);
        return;
    }

    renderKpis(summary, loadedFrom);
}

function renderKpis(summary, loadedFrom) {
    const kpiCards = {
        "total-solar": document.querySelector('[data-kpi="total-solar"]'),
        "total-load": document.querySelector('[data-kpi="total-load"]'),
        "grid-import": document.querySelector('[data-kpi="grid-import"]'),
        "grid-export": document.querySelector('[data-kpi="grid-export"]'),
        "self-consumption": document.querySelector('[data-kpi="self-consumption"]'),
        "net-savings": document.querySelector('[data-kpi="net-savings"]')
    };

    const setValue = (key, value) => {
        const el = kpiCards[key];
        if (el) el.textContent = value;
    };

    if (!summary) {
        Object.keys(kpiCards).forEach((key) => setValue(key, "N/A"));
        return;
    }

    const energy = summary.aggregated_energy || {};
    const financial = summary.aggregated_financial || {};

    const totalSolar = Number(energy.total_solar_kwh || 0);
    const totalLoad = Number(energy.total_load_kwh || 0);
    const gridImport = Number(energy.total_grid_import_kwh || 0);
    const gridExport = Number(energy.total_grid_export_kwh || 0);
    const netProfit = Number(financial.net_profit ?? (Number(financial.total_revenue || 0) - Number(financial.total_cost || 0)));

    const selfConsumption = totalSolar > 0
        ? ((totalSolar - gridExport) / totalSolar) * 100
        : 0;

    setValue("total-solar", formatKwh(totalSolar));
    setValue("total-load", formatKwh(totalLoad));
    setValue("grid-import", formatKwh(gridImport));
    setValue("grid-export", formatKwh(gridExport));
    setValue("self-consumption", `${formatPercent(selfConsumption)}`);
    setValue("net-savings", formatCurrency(netProfit));

    if (loadedFrom) {
        const footer = document.querySelector(".footer-inner span:last-child");
        if (footer) {
            footer.textContent = `Data loaded from ${loadedFrom}`;
        }
    }
}

function formatKwh(value) {
    return `${formatNumber(value, 1)} kWh`;
}

function formatPercent(value) {
    return `${formatNumber(value, 1)}%`;
}

function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2
    }).format(value);
}

function formatNumber(value, digits = 1) {
    return new Intl.NumberFormat("en-US", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    }).format(Number(value || 0));
}
