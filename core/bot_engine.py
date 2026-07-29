from enum import Enum, auto


class BotState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class BotEngine:

    def __init__(self):

        self.state = BotState.STOPPED

        # Aquí registraremos los módulos
        self.modules = []

    # =====================================
    # Control del motor
    # =====================================

    def start(self):

        if self.state == BotState.RUNNING:
            return

        self.state = BotState.RUNNING

        print("Bot iniciado")

    def stop(self):

        self.state = BotState.STOPPED

        print("Bot detenido")

    def pause(self):

        if self.state == BotState.RUNNING:

            self.state = BotState.PAUSED

            print("Bot pausado")

    def resume(self):

        if self.state == BotState.PAUSED:

            self.state = BotState.RUNNING

            print("Bot reanudado")

    # =====================================
    # Game Loop
    # =====================================

    def update(self):

        if self.state != BotState.RUNNING:
            return

        # Ejecutar todos los módulos registrados
        for module in self.modules:
            module.update()

    # =====================================
    # Gestión de módulos
    # =====================================

    def register_module(self, module):

        self.modules.append(module)

    # =====================================
    # Consultas
    # =====================================

    def is_running(self):

        return self.state == BotState.RUNNING

    def is_stopped(self):

        return self.state == BotState.STOPPED

    def is_paused(self):

        return self.state == BotState.PAUSED