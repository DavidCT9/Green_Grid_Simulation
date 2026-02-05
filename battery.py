class Battery:
    def __init__(self, battery_size: float, battery_round_trip_efficiency: float):
        self._state = 100.0 # % -- battery state of charge (SoC) - update it based on the net energy flow (generation - load) at each time step
        self._size = battery_size
        self._efficiency = battery_round_trip_efficiency


