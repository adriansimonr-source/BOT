from abc import ABC, abstractmethod


class BaseModule(ABC):

    def __init__(self, name: str):

        self.name = name
        self.enabled = True

    # =====================================
    # Control
    # =====================================

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def is_enabled(self):
        return self.enabled

    # =====================================
    # Ciclo de vida
    # =====================================

    def on_start(self):
        """Se ejecuta cuando el bot arranca."""
        pass

    def on_stop(self):
        """Se ejecuta cuando el bot se detiene."""
        pass

    # =====================================
    # Game Loop
    # =====================================

    @abstractmethod
    def update(self):
        """Se ejecuta en cada tick del BotEngine."""
        pass