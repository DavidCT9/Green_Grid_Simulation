#  

A digital twin simulation of a solar-equipped home energy system, designed to model energy flow, storage, and costs under various conditions and management strategies.

## Features
- **Component Simulation**: Models Solar Panel, Battery (13.5kWh), Inverter (with failure modes), Grid (with export limits), and variable House Load.
- **Energy Management Strategies (EMS)**:
  - **Load Priority**: Prioritizes powering the house, then charging the battery.
  - **Charge Priority**: Prioritizes filling the battery first.
  - **Produce Priority**: Prioritizes exporting energy to the grid.
- **Dynamic Configuration**: Adjustable simulation parameters via a command-line menu.
- **Detailed Logging**: Supports both Hourly and Daily logging resolutions.
- **Automated Reporting**: Generates statistical summaries and visualizations.

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
- **Configuration**: You will be prompted to use Default values or Customize parameters (e.g., Duration, Battery Size, Costs).
- **Strategy Selection**: Choose your EMS priority (0, 1, or 2).

The simulation runs and saves all data to `log.csv`.

### 2. Generate Report
After running the simulation, execute the reporting module:
```bash
python reporting.py
```
- **Console Output**: Displays Average SOC, Total Generation/Consumption, Financials, and Unmet Load events.
- **Charts**: Generates and saves the following images:
  - `report_soc.png`: Battery State of Charge over time.
  - `report_energy.png`: Energy Balance (Solar, Load, Grid).
  - `report_financial.png`: Total Revenue vs Cost.

## File Structure
- `main.py`: Entry point, simulation loop, configuration, and logging.
- `reporting.py`: Analysis and visualization module.
- `battery.py` / `solar_panel.py` / `inverter.py` / `grid.py` / `house_load.py`: Component models.
- `utils.py`: Helper functions for solar/time calculations.
