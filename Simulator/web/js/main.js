import { state, updateState } from "./state.js";
import { loadDashboardData } from "./dataLoader.js";
import { renderDuckCurve } from "./charts/duckCurve.js";
import { renderProductionChart } from "./charts/productionChart.js";

const d3 = window.d3;

let dashboardData = null;

const KPI_SELECTORS = {
    "total-solar": '[data-kpi="total-solar"]',
    "total-load": '[data-kpi="total-load"]',
    "grid-import": '[data-kpi="grid-import"]',
    "grid-export": '[data-kpi="grid-export"]',
    "self-consumption": '[data-kpi="self-consumption"]',
    "net-savings": '[data-kpi="net-savings"]'
};

document.addEventListener("DOMContentLoaded", async () => {
    setupControls();
    await loadAndRender();

    document.addEventListener("stateChange", () => {
        if (!dashboardData) {
            return;
        }

        console.log("Rendering charts with state:", { ...state });
        renderAllCharts(dashboardData.households);
    });
});

function setupControls() {
    const controls = {
        timeRange: document.getElementById("timeRange"),
        houseType: document.getElementById("houseType"),
        wealthLevel: document.getElementById("wealthLevel"),
        metricView: document.getElementById("metricView")
    };

    Object.entries(controls).forEach(([key, control]) => {
        if (!control) {
            return;
        }

        control.addEventListener("change", () => {
            updateState(key, control.value);
        });
    });

    console.log("Initial state:", { ...state });
}

async function loadAndRender() {
    dashboardData = await loadDashboardData();
    renderKpis(dashboardData.summary, dashboardData.generalInfo, dashboardData.loadedFrom);
    renderAllCharts(dashboardData.households);
}

function renderAllCharts(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
        renderEmptyState();
        return;
    }

    renderProductionChart(rows, state);
    renderDuckCurve(rows, state);
}

function renderKpis(summary, generalInfo, loadedFrom) {
    const kpiCards = Object.fromEntries(
        Object.entries(KPI_SELECTORS).map(([key, selector]) => [key, document.querySelector(selector)])
    );

    const setValue = (key, value) => {
        const element = kpiCards[key];
        if (element) {
            element.textContent = value;
        }
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
    setValue("self-consumption", formatPercent(selfConsumption));
    setValue("net-savings", formatCurrency(netProfit));

    const footer = document.querySelector(".footer-inner span:last-child");
    if (footer) {
        const totalHouses = generalInfo?.total_houses ?? summary?.total_households ?? "unknown";
        footer.textContent = `Data loaded from ${loadedFrom.summary || "summary"} | Houses: ${totalHouses}`;
    }
}

function renderEmptyState() {
    const main = document.getElementById("chart-area-main");
    const duck = document.getElementById("chart-area-duck");
    if (main) {
        main.innerHTML = "<p>No data available.</p>";
    }
    if (duck) {
        duck.innerHTML = "<p>No data available.</p>";
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
