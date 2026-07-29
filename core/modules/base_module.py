import time
from abc import ABC, abstractmethod


class BaseModule(ABC):

    def __init__(self, name: str, interval_ms: int = 100):

        # Nombre del módulo
        self.name = name

        # Estado
        self.enabled = True

        # Intervalo de ejecución (ms)
        self.interval_ms = interval_ms

        # Última ejecución (ms)
        self._last_update = 0.0

    def get_name(self):
        return self.name

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def is_enabled(self):
        return self.enabled

    def set_interval(self, interval_ms: int):
        self.interval_ms = interval_ms

    def get_interval(self):
        return self.interval_ms

    def on_start(self):
        self._last_update = 0.0

    def on_stop(self):
        pass

    def should_update(self) -> bool:

        now = time.perf_counter() * 1000

        if (now - self._last_update) >= self.interval_ms:
            self._last_update = now
            return True

        return False

# Game Loop

    @abstractmethod
    def update(self, state):
        pass