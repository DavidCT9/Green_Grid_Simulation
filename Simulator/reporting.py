import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

LOG_FILE_PATH = BASE_DIR.joinpath("log.csv")
LOG_JSON_PATH = BASE_DIR.joinpath("log.json")
LOG_SUMMARY_PATH = BASE_DIR.joinpath("log_summary.json")
SOC_CHART_PATH = BASE_DIR.joinpath("report_soc.png")
ENERGY_CHART_PATH = BASE_DIR.joinpath("report_energy.png")
FINANCIAL_CHART_PATH = BASE_DIR.joinpath("report_financial.png")

def generate_aggregated_report():
    """Generate report from all households"""
    summary_dir = BASE_DIR.joinpath("summary")
    logs_dir = BASE_DIR.joinpath("logs")
    
    if not logs_dir.exists():
        print("No logs directory found. Please run simulation first.")
        return
    
    # Load general info
    info_path = summary_dir.joinpath("general_info.json")
    if info_path.exists():
        with open(info_path, 'r') as f:
            general_info = json.load(f)
        print("\n" + "="*50)
        print("GREEN GRID - MULTI-HOUSEHOLD SIMULATION REPORT")
        print("="*50)
        print(f"Total Households: {general_info['total_houses']}")
        print(f"Simulation Period: {general_info['simulation_days']} days")
        print("\nHousehold Composition:")
        for htype, count in general_info['households_by_type'].items():
            print(f"  {htype}: {count}")
        print("\nWealth Distribution:")
        for wealth, count in general_info['households_by_wealth'].items():
            print(f"  {wealth}: {count}")
    
    # Aggregate data from all households
    all_households_data = []
    total_solar = 0
    total_load = 0
    total_import = 0
    total_export = 0
    total_revenue = 0
    total_cost = 0
    
    # Process each household log
    for house_dir in sorted(logs_dir.iterdir()):
        if house_dir.is_dir():
            log_file = house_dir.joinpath("log.json")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    all_households_data.append(data)
                    
                    # Aggregate totals
                    for entry in data["data"]:
                        total_solar += entry["solar_generation"]
                        total_load += entry["load_demand"]
                        total_import += entry["grid_import"]
                        total_export += entry["grid_export"]
                        total_revenue += entry["revenue_exported"]
                        total_cost += entry["cost_imported"]
    
    # Save aggregated data
    aggregated = {
        "total_households": len(all_households_data),
        "aggregated_energy": {
            "total_solar_kwh": total_solar,
            "total_load_kwh": total_load,
            "total_grid_import_kwh": total_import,
            "total_grid_export_kwh": total_export,
            "net_grid_import_kwh": total_import - total_export
        },
        "aggregated_financial": {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "net_profit": total_revenue - total_cost
        },
        "households": all_households_data
    }
    
    agg_path = summary_dir.joinpath("aggregated_data.json")
    with open(agg_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    # Print summary
    print("\n" + "-"*50)
    print("AGGREGATED RESULTS")
    print("-"*50)
    print(f"Total Solar Generation:   {total_solar:.2f} kWh")
    print(f"Total House Load:         {total_load:.2f} kWh")
    print(f"Total Grid Import:        {total_import:.2f} kWh")
    print(f"Total Grid Export:        {total_export:.2f} kWh")
    print(f"Total Revenue:            ${total_revenue:.2f}")
    print(f"Total Cost:               ${total_cost:.2f}")
    print(f"Net Profit:               ${total_revenue - total_cost:.2f}")
    print("="*50)
    print(f"Aggregated data saved to: {agg_path}")

if __name__ == "__main__":
    generate_aggregated_report()
