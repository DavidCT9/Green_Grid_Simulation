import random

import simpy
import pandas as pd
import battery
import solar_panel
import house_load
import grid
import inverter

import battery
from utils import (
    hour_of_day,
    day_of_year,
    season_from_day,
    daily_cloud_coverage,
)

# CONFIG
DEFAULT_CONFIG = {
    "LOG_FREQUENCY": False, # False: Hour log, True: Day Log
    "BATTERY_SIZE": 13.5, # kWh
    "PEAK_SOLAR_GENERATION": 5.0, # kW
    "ENERGY_BASE_LOAD": 0.5, # kW
    "RANDOM_SPIKES_MAX": 3.0, # kW
    "BATTERY_ROUND_TRIP_EFFICIENCY": 0.9, # %
    "INVERTER_MAX_OUTPUT_LIMIT": 4.0, # kW
    "GRID_MAX_EXPORT_LIMIT": 2.0, # kW
    "GRID_MAX_IMPORT_LIMIT": 30.0, # kW
    "SIM_DURATION_DAY": 30, # days
    "TIME_STEP_MIN": 60, # minutes
    "INVERTER_FAILURE_FREQUENCY": 0.005, # probability
    "INVERTER_FAILURE_DURATION": random.randint(4,72), # hours (default random)
    "SIM_START_DAY": 0, # Day 0 = Jan 1st
    "COST_ENERGY_EXPORTED": 0.5, # cents/kWh
    "COST_ENERGY_IMPORTED": 0.75, # cents/kWh
    "IS_ZERO_EXPORT": False # bool
}

LOG_DF = pd.DataFrame({
    "Battery state of charge" : pd.Series(dtype=float),
    "Solar generation" : pd.Series(dtype=float),
    "Load demand" : pd.Series(dtype=float),
    "Grid import" : pd.Series(dtype=float),
    "Grid export" : pd.Series(dtype=float),
    "Unmet load" : pd.Series(dtype=bool), 
    "Revenue from exported energy" : pd.Series(dtype=float),
    "Cost of imported energy" : pd.Series(dtype=float),
    "Daily solar generation" : pd.Series(dtype=float),
    "Daily revenue" : pd.Series(dtype=float),
    "Daily import" : pd.Series(dtype=float),
    "Daily export" : pd.Series(dtype=float),
    "Daily cost" : pd.Series(dtype=float),
    "Daily unmet load (count)" : pd.Series(dtype=float),
    "Daily load" : pd.Series(dtype=float),
    "Inverter status": pd.Series(dtype=bool)
})


PRIORITIES = {0:"LOAD_PRIORITY", 1:"CHARGE_PRIORITY", 2:"PRODUCE_PRIORITY"}

CLOUD_COVERAGE = 0.0 
SEASON_CLOUD_PROBS = {
    "Spring": [0.1, 0.3, 0.4, 0.2],
    "Summer": [0.05, 0.15, 0.3, 0.5],
    "Fall":   [0.2, 0.4, 0.3, 0.1],
    "Winter": [0.3, 0.4, 0.2, 0.1],
}

def get_user_config():
    print("\n--- Configuration Menu ---")
    print("1: Use Default Configuration")
    print("2: Customize Configuration")
    choice = input("Enter your choice (1 or 2): ")
    
    config = DEFAULT_CONFIG.copy()
    
    if choice == '2':
        print("\nPress Enter to keep default value.")
        for key, value in config.items():
            user_input = input(f"{key} (Default: {value}): ")
            if user_input:
                try:
                    if isinstance(value, bool):
                        config[key] = user_input.lower() in ('true', '1', 'yes')
                    elif isinstance(value, int):
                        config[key] = int(user_input)
                    else:
                        config[key] = float(user_input)
                except ValueError:
                    print(f"Invalid input for {key}. Keeping default: {value}")
    
    # Recalculate duration min based on inputs
    config["SIM_DURATION_MIN"] = config["SIM_DURATION_DAY"] * 24 * 60
    return config

def home_energy_system(env, battery, panel, load, inverter, grid, priorities, config):
    for i in range(3):
        print(f"{i}: {priorities[i]}")
    priority = int(input("Enter your priority: "))
    print(f"You have chosen {priorities[priority]} \n Starting Simulation...")
    
    current_day = -1
    cloud = 0.0
    daily_solar = 0.0
    revenue_energy_exported = 0.0
    cost_energy_imported = 0.0
    daily_import = 0.0
    daily_export = 0.0
    daily_cost = 0.0
    daily_unmet = 0.0
    daily_revenue = 0.0
    daily_load = 0.0

    sim_duration_days = config["SIM_DURATION_DAY"]
    
    for i in range(sim_duration_days):
        for j in range(24):

            hour = hour_of_day(env)
            day = day_of_year(env, config["SIM_START_DAY"])

            if day != current_day:
                current_day = day
                season = season_from_day(day)
                cloud = daily_cloud_coverage(SEASON_CLOUD_PROBS[season])
            inverter_down = inverter.is_down(env)
            solar_kw = panel.generate(hour, cloud, config["INVERTER_MAX_OUTPUT_LIMIT"], inverter_down)
            load_kw = load.demand(hour)

            solar_kwh = solar_kw
            load_kwh = load_kw
            grid_import = grid_export = unmet = 0.0

            if priority == 0: # Load Priority
                net = solar_kwh - load_kwh
                if net >= 0:
                    charged = battery.charge(net)
                    if grid._is_zero_export and battery._soc == 100:
                        grid_export = 0.0
                    else:
                        grid_export = max(0.0, net - charged)
                else:
                    supplied = battery.discharge(-net)
                    deficit = -net - supplied
                    if deficit > 0:
                        grid_import = deficit
                        if grid_import > grid._import_limit:
                            grid_import = grid._import_limit
                            unmet = grid_import - grid._import_limit
            elif priority == 1: # Charge Priority
                charge_remainder = solar_kwh - battery.charge(solar_kwh)
                net_after_battery = charge_remainder - load_kwh

                if net_after_battery >= 0:
                    if grid._is_zero_export and battery._soc == 100:
                        grid_export = 0.0
                    else:
                        grid_export = grid.export(net_after_battery)
                else:
                    grid_import = -net_after_battery
                    if grid_import > grid._import_limit:
                        grid_import = grid._import_limit
                        unmet = grid_import - grid._import_limit

            elif priority == 2: # Produce Priority
                if grid._is_zero_export and battery._soc == 100:
                    grid_export = 0.0
                else:
                    grid_export = grid.export(solar_kwh)
                remainder = solar_kwh - grid_export
                charged = battery.charge(remainder)
                reminder_for_load = remainder - charged
                net_deficit = load_kwh - reminder_for_load


                provided = battery.discharge(net_deficit)
                still_needed = net_deficit - provided
                grid_import = still_needed # Grid covers the rest
                if grid_import > grid._import_limit:
                    grid_import = grid._import_limit
                    unmet = grid_import - grid._import_limit


            revenue_energy_exported = grid_export * config["COST_ENERGY_EXPORTED"]
            cost_energy_imported = grid_import * config["COST_ENERGY_IMPORTED"]
            total_revenue = revenue_energy_exported - cost_energy_imported
            
            daily_solar += solar_kwh
            daily_import += grid_import
            daily_export += grid_export
            daily_revenue += total_revenue
            daily_cost += cost_energy_imported
            daily_unmet += 0 if unmet == False else 1
            daily_load += load_kwh
                
            log_freq = config["LOG_FREQUENCY"]
            if j == 23 and log_freq:
                write_to_df(battery, solar_kwh, load_kwh, grid_import, grid_export, unmet, revenue_energy_exported, cost_energy_imported, daily_solar, daily_revenue, daily_import, daily_export, daily_cost, daily_unmet, daily_load, inverter_down)
                # Reset accumulators after logging daily values
                daily_solar = 0.0
                daily_import = 0.0
                daily_export = 0.0
                daily_cost = 0.0
                daily_revenue = 0.0
                daily_unmet = 0.0
                daily_load = 0.0
            elif not log_freq:
                write_to_df(battery, solar_kwh, load_kwh, grid_import, grid_export, unmet, revenue_energy_exported, cost_energy_imported, daily_solar, daily_revenue, daily_import, daily_export, daily_cost, daily_unmet, daily_load, inverter_down)
                
            yield env.timeout(config["TIME_STEP_MIN"])

    LOG_DF.to_csv("log.csv", index=False)

def write_to_df(battery, solar_kwh, load_kwh, grid_import, grid_export, unmet, revenue_energy_exported, cost_energy_imported, daily_solar, daily_revenue, daily_import, daily_export, daily_cost, daily_unmet, daily_load, inverter_status):
    unmet = True if unmet > 0 else False
    LOG_DF.loc[len(LOG_DF)] = [
        battery._soc, solar_kwh, load_kwh,
        grid_import, grid_export, unmet,
        revenue_energy_exported, cost_energy_imported,
        daily_solar, daily_revenue, daily_import, 
        daily_export, daily_cost, daily_unmet, 
        daily_load, inverter_status
    ]

if __name__ == "__main__":
    # GET CONFIG
    config = get_user_config()

    # SETTING UP ENVIRONMENT
    env = simpy.Environment()

    # INITIALIZING INSTANCES
    battery = battery.Battery(size_kwh=config["BATTERY_SIZE"], efficiency=config["BATTERY_ROUND_TRIP_EFFICIENCY"])
    panel = solar_panel.SolarPanel(capacity=config["PEAK_SOLAR_GENERATION"])
    load = house_load.HouseLoad(base_load=config["ENERGY_BASE_LOAD"], spikes_max=config["RANDOM_SPIKES_MAX"])
    inverter = inverter.Inverter(output_limit=config["INVERTER_MAX_OUTPUT_LIMIT"], failure_freq=config["INVERTER_FAILURE_FREQUENCY"], failure_duration=config["INVERTER_FAILURE_DURATION"])
    grid = grid.Grid(grid_max_export_limit=config["GRID_MAX_EXPORT_LIMIT"], is_zero_export=config["IS_ZERO_EXPORT"], grid_max_import_limit=config["GRID_MAX_IMPORT_LIMIT"])

    # CALLING SIM METHOD
    env.process(home_energy_system(env, battery, panel, load, inverter, grid, PRIORITIES, config))
    env.run()
    print("Simulation finished. Generating report...")
    import reporting
    reporting.generate_report()
