# house_load.py
import random

class HouseLoad:
    def __init__(self, base_load, spikes_max):
        self._base = base_load
        self._spikes_max = spikes_max

    def demand(self, hour):
        noise = max(0.0, random.normalvariate(0.0, 0.1))

        spike = 0.0
        if 18 <= hour <= 21 and random.random() < 0.4:
            spike = random.uniform(0.5, self._spikes_max)

        return self._base + noise + spike
