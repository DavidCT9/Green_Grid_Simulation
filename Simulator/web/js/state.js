  // state.js

export const state = {
    timeRange: "month",
    houseType: "all",
    wealthLevel: "all",
    metricView: "absolute"
};

export function updateState(key, value) {
    state[key] = value;
    console.log("STATE UPDATED:", state);

    document.dispatchEvent(new CustomEvent("stateChange", { detail: state }));
}
