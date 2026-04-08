export const state = {
    timeRange: "month",
    houseType: "all",
    wealthLevel: "all"
};

export function updateState(key, value) {
    if (!(key in state)) {
        return;
    }

    state[key] = value;
    console.log("STATE UPDATED:", { ...state });

    document.dispatchEvent(
        new CustomEvent("stateChange", {
            detail: { ...state }
        })
    );
}
