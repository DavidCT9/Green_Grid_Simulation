# solar_panel.py
import math
import random

class SolarPanel:
    def __init__(self, capacity):
        self._capacity = capacity
        self._generation = 0.0
        self._hourly_cloud = 0.0

    def generate(self, hour, daily_cloud_base, inverter_limit, inverter_down):
        if inverter_down or hour < 6 or hour > 18:
            self._generation = 0.0
            return 0.0
        
        # Hourly cloud variation
        cloud_variation = random.uniform(-0.3, 0.3)
        hourly_cloud = max(0.0, min(0.95, daily_cloud_base + cloud_variation))
        
        # Possibility of brief heavy cloud coverage (10% chance per hour)
        if random.random() < 0.1:
            hourly_cloud = min(0.95, hourly_cloud + random.uniform(0.2, 0.5))
        
        sun_angle = (hour - 6) * (math.pi / 12)
        raw = self._capacity * math.sin(sun_angle)
        clipped = min(raw, inverter_limit)
        self._generation = clipped * (1 - hourly_cloud)
        return self._generation
