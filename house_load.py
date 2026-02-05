class HouseLoad:
    def __init__(self, energy_base_load: float, random_spikes_max: float):
        self._base_load = energy_base_load
        self._spikes_max = random_spikes_max
