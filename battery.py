# battery.py
class Battery:
    def __init__(self, size_kwh, efficiency, floor=5.0):
        self._size = size_kwh
        self._soc = 100.0
        self._eff = efficiency
        self._floor = floor

    def charge(self, energy):
        stored = energy * self._eff
        max_add = self._size * (100 - self._soc) / 100
        actual = min(stored, max_add)
        self._soc += 100 * actual / self._size
        return actual

    def discharge(self, energy):
        usable = self._size * (self._soc - self._floor) / 100
        actual = min(energy / self._eff, usable)
        self._soc -= 100 * actual / self._size
        return actual
