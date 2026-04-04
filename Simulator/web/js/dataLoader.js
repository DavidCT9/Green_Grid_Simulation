const SUMMARY_PATHS = [
    "./data/summary/aggregated_data.json",
    "./summary/aggregated_data.json"
];

const GENERAL_INFO_PATHS = [
    "./data/summary/general_info.json",
    "./summary/general_info.json"
];

const LOG_BASE_PATHS = [
    "./data/logs",
    "./logs"
];

async function fetchJSON(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Failed to load ${path}: ${response.status}`);
    }
    return response.json();
}

async function fetchFirstAvailable(paths) {
    for (const path of paths) {
        try {
            const data = await fetchJSON(path);
            return { data, path };
        } catch (error) {
            // Try the next candidate.
        }
    }
    return { data: null, path: null };
}

function resolveTotalHouses(summary, generalInfo) {
    const candidates = [
        generalInfo?.total_houses,
        summary?.total_households,
        Array.isArray(summary?.households) ? summary.households.length : null
    ];

    for (const candidate of candidates) {
        const value = Number(candidate);
        if (Number.isFinite(value) && value > 0) {
            return value;
        }
    }

    return 0;
}

function normalizeHouseholdRecords(householdFile) {
    const topLevel = {
        household_id: householdFile.household_id,
        household_type: householdFile.household_type,
        wealth_level: householdFile.wealth_level,
        wealth_multiplier: householdFile.wealth_multiplier,
        base_load: householdFile.base_load,
        spikes_max: householdFile.spikes_max
    };

    return (Array.isArray(householdFile.data) ? householdFile.data : []).map((row) => ({
        ...topLevel,
        timestamp: Number(row.timestamp),
        battery_soc: Number(row.battery_soc),
        solar_generation: Number(row.solar_generation),
        load_demand: Number(row.load_demand),
        grid_import: Number(row.grid_import),
        grid_export: Number(row.grid_export),
        unmet_load: Boolean(row.unmet_load),
        revenue_exported: Number(row.revenue_exported),
        cost_imported: Number(row.cost_imported),
        inverter_status: Boolean(row.inverter_status)
    }));
}

async function loadHouseholdsFromLogs(totalHouses) {
    if (!totalHouses) {
        return [];
    }

    const records = [];
    const attempts = [];

    for (let houseId = 1; houseId <= totalHouses; houseId += 1) {
        let loaded = false;

        for (const basePath of LOG_BASE_PATHS) {
            const logPath = `${basePath}/house_${houseId}/log.json`;
            try {
                const householdFile = await fetchJSON(logPath);
                records.push(...normalizeHouseholdRecords(householdFile));
                loaded = true;
                break;
            } catch (error) {
                attempts.push(logPath);
            }
        }

        if (!loaded) {
            console.warn(`Could not load log for house ${houseId}`);
        }
    }

    if (records.length === 0) {
        console.warn("No household logs were loaded.");
    }

    return records;
}

function fallbackFlattenHouseholds(summary) {
    if (!summary || !Array.isArray(summary.households)) {
        return [];
    }

    return summary.households.flatMap(normalizeHouseholdRecords);
}

export async function loadDashboardData() {
    const [summaryResult, generalInfoResult] = await Promise.all([
        fetchFirstAvailable(SUMMARY_PATHS),
        fetchFirstAvailable(GENERAL_INFO_PATHS)
    ]);

    const summary = summaryResult.data;
    const generalInfo = generalInfoResult.data;
    const totalHouses = resolveTotalHouses(summary, generalInfo);

    let households = await loadHouseholdsFromLogs(totalHouses);
    if (households.length === 0) {
        households = fallbackFlattenHouseholds(summary);
    }

    console.log("Loaded dashboard data:", {
        summaryPath: summaryResult.path,
        generalInfoPath: generalInfoResult.path,
        totalHouses,
        records: households.length
    });

    return {
        summary,
        generalInfo,
        households,
        loadedFrom: {
            summary: summaryResult.path,
            generalInfo: generalInfoResult.path
        }
    };
}
