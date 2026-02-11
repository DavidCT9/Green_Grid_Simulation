# solar_panel.py
import math

class SolarPanel:
    def __init__(self, capacity):
        self._capacity = capacity
        self._generation = 0.0

    def generate(self, hour, cloud_coverage, inverter_limit, inverter_down):
        if inverter_down or hour < 6 or hour > 18:
            self._generation = 0.0
            return 0.0

        sun_angle = (hour - 6) * (math.pi / 12)
        raw = self._capacity * math.sin(sun_angle)
        clipped = min(raw, inverter_limit)
        self._generation = clipped * (1 - cloud_coverage)
        return self._generation
