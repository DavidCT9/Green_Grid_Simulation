import simpy
import json
import random
from pathlib import Path

class HouseholdSimulator:
    def __init__(self, household_id, household_type, wealth_level, config, household_config, base_dir):
        self.id = household_id
        self.type = household_type
        self.wealth_level = wealth_level
        self.config = config
        self.household_config = household_config
        self.base_dir = base_dir
        
        # Create log directory for this house
        self.log_dir = base_dir.joinpath("web/data/logs", f"house_{household_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.battery = None
        self.panel = None
        self.load = None
        self.inverter = None
        self.grid = None
        self.log_data = []
        
    def initialize(self):
        """Initialize all components for this household"""
        # Import here to avoid circular imports
        import battery, solar_panel, house_load, inverter, grid
        
        # Get household-specific parameters from config
        household_params = self.household_config["households"][self.type]
        wealth_multiplier = self.household_config["wealth_multipliers"][self.wealth_level]
        
        # Calculate adjusted base load
        base_load = household_params["base_load"] * wealth_multiplier
        spikes_max = household_params["spikes_max"] * wealth_multiplier
        
        # Initialize components
        self.battery = battery.Battery(
            size_kwh=self.config["BATTERY_SIZE"],
            efficiency=self.config["BATTERY_ROUND_TRIP_EFFICIENCY"]
        )
        self.panel = solar_panel.SolarPanel(
            capacity=self.config["PEAK_SOLAR_GENERATION"]
        )
        self.load = house_load.HouseLoad(
            base_load=base_load,
            spikes_max=spikes_max
        )
        self.inverter = inverter.Inverter(
            output_limit=self.config["INVERTER_MAX_OUTPUT_LIMIT"],
            failure_freq=self.config["INVERTER_FAILURE_FREQUENCY"],
            failure_duration=self.config["INVERTER_FAILURE_DURATION"]
        )
        self.grid = grid.Grid(
            grid_max_export_limit=self.config["GRID_MAX_EXPORT_LIMIT"],
            is_zero_export=self.config["IS_ZERO_EXPORT"],
            grid_max_import_limit=self.config["GRID_MAX_IMPORT_LIMIT"]
        )
    
    def run_simulation(self, env, priority, season_cloud_probs, start_day):
        """Run the simulation for this household"""
        current_day = -1
        current_season = None
        daily_cloud_base = 0.0
        
        # Accumulators for daily values
        daily_solar = 0.0
        daily_import = 0.0
        daily_export = 0.0
        daily_cost = 0.0
        daily_revenue = 0.0
        daily_unmet = 0.0
        daily_load = 0.0
        
        sim_duration_days = self.config["SIM_DURATION_DAY"]
        
        for day in range(sim_duration_days):
            for hour in range(24):
                sim_hour = env.now / 60 % 24
                sim_day = start_day + int(env.now / (60 * 24))
                day_of_week = sim_day % 7
                
                if sim_day != current_day:
                    current_day = sim_day
                    current_season = self._get_season(sim_day)
                    daily_cloud_base = self._get_daily_cloud(season_cloud_probs[current_season])
                
                inverter_down = self.inverter.is_down(env)
                solar_kw = self.panel.generate(
                    sim_hour, daily_cloud_base,
                    self.config["INVERTER_MAX_OUTPUT_LIMIT"], inverter_down
                )
                load_kw = self.load.demand(sim_hour, day_of_week, current_season)
                
                grid_import, grid_export, unmet = self._process_energy_flow(
                    solar_kw, load_kw, priority
                )
                
                revenue = grid_export * self.config["COST_ENERGY_EXPORTED"]
                cost = grid_import * self.config["COST_ENERGY_IMPORTED"]
                
                daily_solar += solar_kw
                daily_import += grid_import
                daily_export += grid_export
                daily_cost += cost
                daily_revenue += revenue - cost
                daily_unmet += 1 if unmet > 0 else 0
                daily_load += load_kw
                
                # Log data
                self._log_data(
                    self.battery._soc, solar_kw, load_kw,
                    grid_import, grid_export, unmet,
                    revenue, cost,
                    daily_solar, daily_revenue, daily_import,
                    daily_export, daily_cost, daily_unmet,
                    daily_load, inverter_down
                )

                yield env.timeout(self.config["TIME_STEP_MIN"])
        
        self._save_log()
    
    def _process_energy_flow(self, solar, load, priority):
        """Process energy flow based on priority"""
        grid_import = grid_export = unmet = 0.0
        
        if priority == 0:  # Load Priority
            net = solar - load
            if net >= 0:
                charged = self.battery.charge(net)
                if self.grid._is_zero_export and self.battery._soc == 100:
                    grid_export = 0.0
                else:
                    grid_export = max(0.0, net - charged)
            else:
                supplied = self.battery.discharge(-net)
                deficit = -net - supplied
                if deficit > 0:
                    grid_import = min(deficit, self.grid._import_limit)
                    unmet = deficit - grid_import
        
        elif priority == 1:  # Charge Priority
            charge_remainder = solar - self.battery.charge(solar)
            net_after_battery = charge_remainder - load
            
            if net_after_battery >= 0:
                if self.grid._is_zero_export and self.battery._soc == 100:
                    grid_export = 0.0
                else:
                    grid_export = self.grid.export(net_after_battery)
            else:
                grid_import = min(-net_after_battery, self.grid._import_limit)
                unmet = -net_after_battery - grid_import
        
        elif priority == 2:  # Produce Priority
            if self.grid._is_zero_export and self.battery._soc == 100:
                grid_export = 0.0
            else:
                grid_export = self.grid.export(solar)
            
            remainder = solar - grid_export
            charged = self.battery.charge(remainder)
            reminder_for_load = remainder - charged
            net_deficit = max(0, load - reminder_for_load)
            
            provided = self.battery.discharge(net_deficit)
            still_needed = net_deficit - provided
            grid_import = min(still_needed, self.grid._import_limit)
            unmet = still_needed - grid_import
        
        return grid_import, grid_export, unmet
    
    def _get_season(self, day):
        """Get season from day of year"""
        if 80 <= day < 172:
            return "Spring"
        if 172 <= day < 264:
            return "Summer"
        if 264 <= day < 355:
            return "Fall"
        return "Winter"
    
    def _get_daily_cloud(self, season_probs):
        """Generate daily cloud coverage"""
        from utils import daily_cloud_coverage
        return daily_cloud_coverage(season_probs)
    
    def _log_data(self, *args):
        """Store log data in memory"""
        log_entry = {
            "timestamp": len(self.log_data),
            "battery_soc": args[0],
            "solar_generation": args[1],
            "load_demand": args[2],
            "grid_import": args[3],
            "grid_export": args[4],
            "unmet_load": args[5] > 0,
            "revenue_exported": args[6],
            "cost_imported": args[7],
            "daily_solar": args[8],
            "daily_revenue": args[9],
            "daily_import": args[10],
            "daily_export": args[11],
            "daily_cost": args[12],
            "daily_unmet": args[13],
            "daily_load": args[14],
            "inverter_status": args[15]
        }
        self.log_data.append(log_entry)
    
    def _save_log(self):
        """Save log data to JSON file"""
        # Add metadata to log
        log_with_metadata = {
            "household_id": self.id,
            "household_type": self.type,
            "wealth_level": self.wealth_level,
            "wealth_multiplier": self.household_config["wealth_multipliers"][self.wealth_level],
            "base_load": self.load._base,
            "spikes_max": self.load._spikes_max,
            "data": self.log_data
        }
        
        log_path = self.log_dir.joinpath("log.json")
        with open(log_path, 'w') as f:
            json.dump(log_with_metadata, f, indent=2)
        
        return log_with_metadata
