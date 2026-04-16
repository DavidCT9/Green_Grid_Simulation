#  

A digital twin simulation of a solar-equipped home energy system, designed to model energy flow, storage, and costs under various conditions and management strategies across 100 households with different types and wealth levels.

## Features
- **Multi-Household Simulation**: Simulates 100 households simultaneously using SimPy, each with independent energy behavior.
- **Household Types**: Studio, Small, and Large Family, each with different base loads and spike patterns.
- **Component Simulation**: Models Solar Panel, Battery (13.5kWh), Inverter (with failure modes), Grid (with export limits), and variable House Load.
- **Energy Management Strategies (EMS)**:
  - **Load Priority**: Prioritizes powering the house, then charging the battery.
  - **Charge Priority**: Prioritizes filling the battery first.
  - **Produce Priority**: Prioritizes exporting energy to the grid.
- **Dynamic Configuration**: Adjustable simulation parameters via a command-line menu.
- **Detailed Logging**: Supports both Hourly and Daily logging resolutions.
- **Automated Reporting**: Generates statistical summaries and visualizations.
- **Interactive Dashboard**: Visualizes energy balance, duck curve, grid flow, household segmentation by type and wealth level, battery behaviour/inverter impact, batery use, costs, revenues and savings, and the enrgy balance breakdown.


## Requirements
- Python 3.8+
- Dependencies:
  - `simpy`
  - `pandas`
  - `matplotlib`
  - `seaborn`

## Installation
1. Ensure Python is installed.
2. Install required packages:
   ```bash
   pip install simpy pandas matplotlib seaborn
   ```

## Usage

### 1. Run the Simulation
Execute the main script to start the simulation:
```bash
python main.py
```

The simulation runs and saves all data to `log.csv`.

### 2. How to view the dashboard
Go to the `Simulator/web` folder in VS Code, right-click index.html and select Open with Live Server. The dashboard will open automatically in your browser at `localhost:5500`. If you cant see this option, you need to download the Live Server extension in VS Code.

### Configuration 
**`config_default.json`**: Controls the base simulation parameters:
- Battery size 
- Peak solar generation capacity
- Base energy load and random spike limits
- Inverter output limit and failure settings
- Grid import/export limits
- Simulation duration and start day
- Energy cost and revenue rates
- Zero export mode 

**`config_houses.json`**: Controls the neighborhood composition:
- Number of households per type (studio, small family, large family)
- Base load and spike max per household type
- Wealth level distribution across the neighborhood
- Consumption multipliers per wealth level

Note: `config_user.json` exists in the repository but is not used by the simulation.

## File Structure
- `main.py`: Entry point, simulation loop, configuration, and logging.
- `household_simulator.py `
- `battery.py` / `solar_panel.py` / `inverter.py` / `grid.py` / 
- `house_load.py`: Component models.
- `utils.py`: Helper functions for solar/time calculations.
-  `config_default.json` `config_houses.json`
```
web/
└── data/
    ├── summary/
    │   ├── general_info.json       # Simulation metadata
    │   └── aggregated_data.json    # Neighborhood-level totals
    └── logs/
        └── house_#/
            └── log.json            # Per-household hourly log
```