from mlModel.solar_predictor import get_predictor

class SolarPanel:
    def __init__(self, capacity):
        self._capacity = capacity
        self._generation = 0.0
        self._predictor = get_predictor()

    def generate(self, hour, daily_cloud_base, inverter_limit, inverter_down, sim_day=0):
        if inverter_down:
            self._generation = 0.0
            return 0.0

        self._generation = self._predictor.predict_kw(
            sim_day=sim_day,
            hour=hour,
            peak_solar_generation_kw=self._capacity,
        )
        return self._generation
