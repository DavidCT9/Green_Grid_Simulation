import random
import json
import simpy
from pathlib import Path
from household_simulator import HouseholdSimulator
from utils import season_from_day, SEASON_CLOUD_PROBS  # Need to export SEASON_CLOUD_PROBS

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR.joinpath("config_default.json")
USER_CONFIG_PATH = BASE_DIR.joinpath("config_user.json")
HOUSES_CONFIG_PATH = BASE_DIR.joinpath("config_houses.json")

def load_config_from_json(file_path):
    """Load configuration from a JSON file"""
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
        
        if config.get("INVERTER_FAILURE_DURATION") == "random":
            config["INVERTER_FAILURE_DURATION"] = random.randint(4, 72)
        
        config["SIM_DURATION_MIN"] = config["SIM_DURATION_DAY"] * 24 * 60
        
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not valid JSON.")
        return None

def load_houses_config():
    """Load household configuration"""
    if not HOUSES_CONFIG_PATH.exists():
        print(f"Error: {HOUSES_CONFIG_PATH} not found. Creating default...")
        create_default_houses_config()
    
    try:
        with open(HOUSES_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading houses config: {e}")
        return None

def create_default_houses_config():
    """Create default household configuration"""
    default_config = {
        "households": {
            "studio": {"count": 20, "base_load": 0.2, "spikes_max": 2.5},
            "small_family": {"count": 50, "base_load": 0.4, "spikes_max": 4.5},
            "large_family": {"count": 30, "base_load": 0.8, "spikes_max": 7.0}
        },
        "wealth_distribution": {
            "low": 0.20,
            "middle": 0.50,
            "high": 0.25,
            "luxury": 0.05
        },
        "wealth_multipliers": {
            "low": 0.8,
            "middle": 1.0,
            "high": 1.2,
            "luxury": 1.5
        }
    }
    
    with open(HOUSES_CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=2)
    print(f"Created default household configuration: {HOUSES_CONFIG_PATH}")

def generate_households(houses_config):
    """Generate list of households based on configuration"""
    households = []
    household_id = 1
    
    wealth_levels = list(houses_config["wealth_distribution"].keys())
    wealth_probs = list(houses_config["wealth_distribution"].values())
    
    for house_type, params in houses_config["households"].items():
        count = params["count"]
        for _ in range(count):
            wealth_level = random.choices(wealth_levels, weights=wealth_probs)[0]
            households.append({
                "id": household_id,
                "type": house_type,
                "wealth_level": wealth_level,
                "base_load": params["base_load"],
                "spikes_max": params["spikes_max"]
            })
            household_id += 1
    
    return households

def save_general_info(households, config, houses_config):
    """Save general information about the simulation run"""
    summary_dir = BASE_DIR.joinpath("summary")
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    # Count households by type and wealth
    type_counts = {}
    wealth_counts = {}
    for h in households:
        type_counts[h["type"]] = type_counts.get(h["type"], 0) + 1
        wealth_counts[h["wealth_level"]] = wealth_counts.get(h["wealth_level"], 0) + 1
    
    general_info = {
        "total_houses": len(households),
        "simulation_days": config["SIM_DURATION_DAY"],
        "time_step_minutes": config["TIME_STEP_MIN"],
        "households_by_type": type_counts,
        "households_by_wealth": wealth_counts,
        "wealth_distribution_config": houses_config["wealth_distribution"],
        "wealth_multipliers": houses_config["wealth_multipliers"],
        "simulation_config": {
            "battery_size_kwh": config["BATTERY_SIZE"],
            "peak_solar_kw": config["PEAK_SOLAR_GENERATION"],
            "inverter_limit_kw": config["INVERTER_MAX_OUTPUT_LIMIT"],
            "grid_export_limit_kw": config["GRID_MAX_EXPORT_LIMIT"],
            "grid_import_limit_kw": config["GRID_MAX_IMPORT_LIMIT"]
        }
    }
    
    info_path = summary_dir.joinpath("general_info.json")
    with open(info_path, "w") as f:
        json.dump(general_info, f, indent=2)
    print(f"General info saved to: {info_path}")

if __name__ == "__main__":
    print("\n--- Loading Configurations ---")
    
    # Get base simulation config
    base_config = load_config_from_json(DEFAULT_CONFIG_PATH)
    if not base_config:
        print("Failed to load base configuration. Exiting.")
        exit(1)
    
    # Load household configuration
    houses_config = load_houses_config()
    if not houses_config:
        print("Failed to load household configuration. Exiting.")
        exit(1)
    
    # Generate households
    households = generate_households(houses_config)
    print(f"\nGenerated {len(households)} households:")
    type_counts = {}
    for h in households:
        type_counts[h["type"]] = type_counts.get(h["type"], 0) + 1
    for house_type, count in type_counts.items():
        print(f"  - {house_type}: {count}")
    
    save_general_info(households, base_config, houses_config)
    
    # Get priority from user
    print("\n" + "="*50)
    print("PRIORITY SELECTION (applies to all households)")
    print("0: LOAD_PRIORITY - Serve load first, then charge battery, then export")
    print("1: CHARGE_PRIORITY - Charge battery first, then serve load, then export")
    print("2: PRODUCE_PRIORITY - Export first, then charge, then serve load")
    print("="*50)
    
    while True:
        try:
            priority = int(input("Enter your priority (0, 1, or 2): "))
            if priority in [0, 1, 2]:
                break
            else:
                print("Please enter 0, 1, or 2.")
        except ValueError:
            print("Please enter a valid number.")
    
    env = simpy.Environment()
    
    print(f"\nStarting simulation for {len(households)} households...")
    print("This may take a while...\n")
    
    for household in households:
        simulator = HouseholdSimulator(
            household_id=household["id"],
            household_type=household["type"],
            wealth_level=household["wealth_level"],
            config=base_config,
            household_config=houses_config,
            base_dir=BASE_DIR
        )
        simulator.initialize()
        
        env.process(simulator.run_simulation(
            env, priority, SEASON_CLOUD_PROBS, base_config["SIM_START_DAY"]
        ))
    
    env.run()
    
    print("\n" + "="*50)
    print("SIMULATION COMPLETE!")
    print(f"Simulated {len(households)} households for {base_config['SIM_DURATION_DAY']} days")
    print("Logs saved in: logs/")
    print("Summary saved in: summary/")
    print("="*50)
    
    print("\nGenerating aggregated report...")
    import reporting
    reporting.generate_aggregated_report()
