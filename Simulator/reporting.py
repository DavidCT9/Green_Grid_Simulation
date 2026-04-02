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

def generate_report():
    df = None
    if LOG_JSON_PATH.exists():
        print("Loading simulation log from JSON...")
        try:
            with open(LOG_JSON_PATH, 'r') as f:
                log_data = json.load(f)
            df = pd.DataFrame(log_data)
            print("Successfully loaded JSON log.")
        except Exception as e:
            print(f"Error loading JSON: {e}")
    
    if df is None and LOG_FILE_PATH.exists():
        print("Loading simulation log from CSV...")
        df = pd.read_csv(LOG_FILE_PATH)
        print("Successfully loaded CSV log.")
    
    if df is None:
        print(f"Error: No log files found. Please run the simulation first (main.py).")
        return
    
    # Detect Logic Frequency
    is_hourly = len(df) > 60 
    freq_str = "HOURLY" if is_hourly else "DAILY"
    print(f"Detected Log Frequency: {freq_str}")

    # --- Calculations ---
    report_data = {}

    # 1. State of Charge
    report_data["avg_soc"] = df["Battery state of charge"].mean()
    report_data["min_soc"] = df["Battery state of charge"].min()
    report_data["max_soc"] = df["Battery state of charge"].max()

    # 2. Energy Totals
    if is_hourly:
        # Summing hourly columns
        report_data["total_solar"] = df["Solar generation"].sum()
        report_data["total_load"] = df["Load demand"].sum()
        report_data["total_import"] = df["Grid import"].sum()
        report_data["total_export"] = df["Grid export"].sum()
        report_data["total_revenue"] = df["Revenue from exported energy"].sum()
        report_data["total_cost"] = df["Cost of imported energy"].sum()
        report_data["unmet_count"] = df["Unmet load"].sum() # True=1, False=0
    else:
        # Summing daily accumulated columns
        report_data["total_solar"] = df["Daily solar generation"].sum()
        report_data["total_load"] = df["Daily load"].sum()
        report_data["total_import"] = df["Daily import"].sum()
        report_data["total_export"] = df["Daily export"].sum()
        report_data["total_revenue"] = df["Daily revenue"].sum()
        report_data["total_cost"] = df["Daily cost"].sum()
        report_data["unmet_count"] = df["Daily unmet load (count)"].sum()

    report_data["net_profit"] = report_data["total_revenue"] - report_data["total_cost"]
    
    # 3. Inverter Status
    if "Inverter status" in df.columns:
        failures_count = df["Inverter status"].sum()
        report_data["inverter_failures_ticks"] = failures_count
        report_data["inverter_health"] = (1 - (failures_count / len(df))) * 100
    else:
        report_data["inverter_failures_ticks"] = 0
        report_data["inverter_health"] = 100

    # --- PRINT TEXT REPORT ---
    print("\n" + "="*40)
    print(f"   GREEN GRID SIMULATION REPORT ({freq_str})")
    print("="*40)
    print(f"Average Battery SOC:      {report_data['avg_soc']:.2f} %")
    print(f"Min/Max SOC:              {report_data['min_soc']:.2f}% / {report_data['max_soc']:.2f}%")
    print("-" * 40)
    print(f"Total Solar Generation:   {report_data['total_solar']:.2f} kWh")
    print(f"Total House Load:         {report_data['total_load']:.2f} kWh")
    print("-" * 40)
    print(f"Total Grid Import:        {report_data['total_import']:.2f} kWh")
    print(f"Total Grid Export:        {report_data['total_export']:.2f} kWh")
    print("-" * 40)
    print(f"Total Revenue (Export):   ${report_data['total_revenue']:.2f}")
    print(f"Total Cost (Import):      ${report_data['total_cost']:.2f}")
    print(f"NET PROFIT:               ${report_data['net_profit']:.2f}")
    print("-" * 40)
    print(f"Unmet Load Events:        {report_data['unmet_count']}")
    print(f"Inverter 'Down' Ticks:    {report_data['inverter_failures_ticks']}")
    print("="*40 + "\n")

    # --- VISUALIZATIONS ---
    sns.set_theme(style="whitegrid")
    
    # 1. State of Charge Over Time
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["Battery state of charge"], label="SOC %", color="green")
    plt.title("Battery State of Charge Over Time")
    plt.xlabel("Time Step (Hour/Day)")
    plt.ylabel("SOC (%)")
    plt.axhline(y=0, color='r', linestyle='--')
    plt.axhline(y=100, color='r', linestyle='--')
    plt.legend()
    plt.savefig(SOC_CHART_PATH)
    print(f"Saved chart: {SOC_CHART_PATH}")
    plt.close()
    
    # 2. Energy Balance (Line Chart)
    plt.figure(figsize=(10, 5))
    if is_hourly:
        plt.plot(df.index, df["Solar generation"], label="Solar", alpha=0.7)
        plt.plot(df.index, df["Load demand"], label="Load", alpha=0.7)
        plt.plot(df.index, df["Grid import"], label="Import", alpha=0.5)
        plt.plot(df.index, df["Grid export"], label="Export", alpha=0.5)
    else:
         plt.plot(df.index, df["Daily solar generation"], label="Solar", alpha=0.7)
         plt.plot(df.index, df["Daily load"], label="Load", alpha=0.7)
         plt.plot(df.index, df["Daily import"], label="Import", alpha=0.5)
         plt.plot(df.index, df["Daily export"], label="Export", alpha=0.5)
         
    plt.title("Energy Balance Over Time")
    plt.xlabel("Time Step")
    plt.ylabel("Energy (kWh)")
    plt.legend()
    plt.savefig(ENERGY_CHART_PATH)
    print(f"Saved chart: {ENERGY_CHART_PATH}")
    plt.close()

    # 3. Financial Overview (Bar Chart)
    plt.figure(figsize=(6, 6))
    plt.bar(["Revenue", "Cost"], [report_data["total_revenue"], report_data["total_cost"]], color=["green", "red"])
    plt.title("Financial Overview")
    plt.ylabel("Currency ($)")
    plt.savefig(FINANCIAL_CHART_PATH)
    print(f"Saved chart: {FINANCIAL_CHART_PATH}")
    plt.close()

    print("\nReporting complete.")

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
    generate_report()
