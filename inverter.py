class Inverter:
    def __init__(self, inverter_max_output_limit: float, inverter_failure_frequency:float, inverter_failure_duration:int):
        self._output_limit = inverter_max_output_limit
        self._failure_frequency = inverter_failure_frequency
        self._failure_duration = inverter_failure_duration
