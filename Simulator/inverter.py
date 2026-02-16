# inverter.py
import random

class Inverter:
    def __init__(self, output_limit, failure_freq, failure_duration):
        self._limit = output_limit
        self._failure_freq = failure_freq # Already in hours
        self._failure_duration = failure_duration
        self._down_until = -1

    def is_down(self, env):
        if env.now < self._down_until:
            return True

        if random.random() < self._failure_freq / 24:
            self._down_until = env.now + self._failure_duration
            return True

        return False
