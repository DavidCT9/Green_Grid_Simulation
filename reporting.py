import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

LOG_FILE = "log.csv"

def generate_report():
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Please run the simulation first (main.py).")
        return

    print("Loading simulation log...")
    df = pd.read_csv(LOG_FILE)
    
    # Detect Logic Frequency
    # If the simulation is ~30 days, Daily logs will have ~30 rows. Hourly ~720 rows.
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
    # Inverter status is boolean. 
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
    plt.savefig("report_soc.png")
    print("Saved chart: report_soc.png")
    
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
    plt.savefig("report_energy.png")
    print("Saved chart: report_energy.png")

    # 3. Financial Overview (Bar Chart)
    plt.figure(figsize=(6, 6))
    plt.bar(["Revenue", "Cost"], [report_data["total_revenue"], report_data["total_cost"]], color=["green", "red"])
    plt.title("Financial Overview")
    plt.ylabel("Currency ($)")
    plt.savefig("report_financial.png")
    print("Saved chart: report_financial.png")

    print("\nReporting complete.")

if __name__ == "__main__":
    generate_report()
