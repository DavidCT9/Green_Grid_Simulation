# house_load.py
import random

class HouseLoad:
    def __init__(self, base_load, spikes_max):
        self._base = base_load
        self._spikes_max = spikes_max

    def demand(self, hour, day_of_week, season):
        load = self._base
        
        # Weekend adjustment (Saturday=5, Sunday=6)
        if day_of_week >= 5:
            load *= 1.3

        # Seasonal adjustments for AC and heating
        if season == "Summer":
            load *= 1.5
        elif season == "Winter":
            load *= 1.6
        
        # Random noise
        noise = max(0.0, random.normalvariate(0.0, 0.1))
        load += noise
        
        # Evening spikes
        spike = 0.0
        if 18 <= hour <= 21:
            spike_prob = 0.6 if day_of_week >= 5 else 0.4
            if random.random() < spike_prob:
                spike = random.uniform(0.5, self._spikes_max)
        load += spike
        
        appliance_load = self._get_appliance_load(hour, day_of_week)
        load += appliance_load
        
        return load
    
    def _get_appliance_load(self, hour, day_of_week):
        """Generate random appliance usage events"""
        appliances = {
            "washing_machine": (1.5, 2, 0.02),   # 1.5kW for 2 hours, 2% chance per hour
            "dishwasher": (1.2, 1.5, 0.03),      # 1.2kW for 1.5 hours, 3% chance per hour
            "ev_charger": (7.0, 4, 0.01)         # 7kW for 4 hours, 1% chance per hour
        }
        
        if not hasattr(self, '_active_appliances'):
            self._active_appliances = {}
        
        finished = []
        for appliance, (remaining, power) in self._active_appliances.items():
            remaining -= 1
            if remaining <= 0:
                finished.append(appliance)
            else:
                self._active_appliances[appliance] = (remaining, power)
        
        # Remove finished appliances
        for appliance in finished:
            del self._active_appliances[appliance]
        
        # Start new appliances
        for appliance, (power, duration, prob) in appliances.items():
            if appliance not in self._active_appliances:
                actual_prob = prob * 1.5 if day_of_week >= 5 else prob
                if random.random() < actual_prob:
                    self._active_appliances[appliance] = (duration, power)
        
        total_load = sum(power for _, power in self._active_appliances.values())
        
        return total_load
