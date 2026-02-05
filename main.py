import random

import simpy
import pandas as pd
from pyarrow import int32

# CONFIG
LOG_HOUR = pd.DataFrame({
    "Battery state of charge" : pd.Series(dtype=float),
    "Solar generation" : pd.Series(dtype=float),
    "Load demand" : pd.Series(dtype=float),
    "Grid import" : pd.Series(dtype=float),
    "Grid export" : pd.Series(dtype=float),
    "Unmet load" : pd.Series(dtype=bool),
})
LOG_DAY = pd.DataFrame({
    "Battery state of charge" : pd.Series(dtype=float),
    "Solar generation" : pd.Series(dtype=float),
    "Load demand" : pd.Series(dtype=float),
    "Grid import" : pd.Series(dtype=float),
    "Grid export" : pd.Series(dtype=float),
    "Unmet load" : pd.Series(dtype=int32()),
})
BATTERY_SIZE = 13.5 # kWh
PEAK_SOLAR_GENERATION = 5 #kW
ENERGY_BASE_LOAD = 0.5 # kW -- Base consumption of household electronics
RANDOM_SPIKES_MAX = 3 # kW --  random energy consumption spikes during peak hours (6-9 PM).
BATTERY_ROUND_TRIP_EFFICIENCY = 0.9 # % -- Ensure to account for round-trip efficiency losses during charging and discharging
INVERTER_MAX_OUTPUT_LIMIT = 4.0 # kW -- The inverter should have a maximum output limit. If solar generation exceeds this limit, the excess energy is lost (clipped).
GRID_MAX_EXPORT_LIMIT = 20.0 # kW

LOAD_PRIORITY = ["HOUSE_LOAD","BATTERY", "GRID"] # Power the house load first, charge the battery second, export any excess to the grid last.
CHARGE_PRIORITY = ["BATTERY","HOUSE_LOAD", "GRID"] # Charge the battery first, power the house load second, export any excess to the grid last
PRODUCE_PRIORITY = ["EXPORT_UP_TO_THRESHOLD", "BATTERY", "HOUSE_LOAD"] # Export all energy up to threshold first, charge the battery second, power the house load last.
# If the battery is full and the house load is low, curtail solar generation (zero export)

CLOUD_COVERAGE = 0.0 # parameter (0-1) that reduces solar generation proportionally.
# (Clear, Partly Cloudy, Mostly Cloudy, Overcast) - These are the probability factors based on seasons
Spring = [0.1, 0.3, 0.4, 0.2]
Summer = [0.05, 0.15, 0.3, 0.5]
Fall = [0.2, 0.4, 0.3, 0.1]
Winter = [0.3, 0.4, 0.2, 0.1]

SOLAR_PANEL_CAPACITY = 10.0 # kW
# Load profile characteristics (base load, peak load, variability)
SIM_DURATION = 7 # days
TIME_STEP = 60 # minutes
INVERTER_FAILURE_FREQUENCY = 0.005 # energy inverter should have a random failure event that occurs on average once every 200 days (0.5%)
INVERTER_FAILURE_DURATION = random.randint(4,72) #  lasting for a random duration between 4 and 72 hours. During this failure, solar generation is zero regardless of conditions.
SIM_START_DAY = 0 # (1st Jan) # -- Day fo the year to start sim -- Season/month for simulation
COST_ENERGY_EXPORTED = 0.5 # cents per kWh
COST_ENERGY_IMPORTED = 0.75 # cents per kWh
SIM_TOTAL_DAYS = 30 # Your simulation should run for at least a total of 30 simulated days (720 hours)


# sun_angle = time_of_day * (math.pi / 12)
# generation = PEAK_SOLAR_GENERATION * math.sin(sun_angle)