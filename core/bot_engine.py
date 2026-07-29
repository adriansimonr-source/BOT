from enum import Enum, auto

from core.modules.auto_target import AutoTarget
from core.modules.auto_attack import AutoAttack
from core.modules.auto_loot import AutoLoot
from core.modules.buff_manager import BuffManager
from core.modules.rotation_manager import RotationManager

from core.managers.game_state_manager import GameStateManager


class BotState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class BotEngine:

    def __init__(self, game_state_manager: GameStateManager):

        self.state = BotState.STOPPED

        self.game_state_manager = game_state_manager

        # ===========================
        # Módulos
        # ===========================

        self.modules = []

        self.register_module(AutoTarget())
        self.register_module(AutoAttack())
        self.register_module(BuffManager())
        self.register_module(RotationManager())
        self.register_module(AutoLoot())

    # ==================================================
    # Gestión de módulos
    # ==================================================

    def register_module(self, module):

        self.modules.append(module)

    # ==================================================
    # Control del bot
    # ==================================================

    def start(self):

        if self.state == BotState.RUNNING:
            return

        self.state = BotState.RUNNING

        for module in self.modules:
            module.on_start()

        print("Bot iniciado")

    def stop(self):

        if self.state == BotState.STOPPED:
            return

        self.state = BotState.STOPPED

        for module in self.modules:
            module.on_stop()

        print("Bot detenido")

    def pause(self):

        if self.state != BotState.RUNNING:
            return

        self.state = BotState.PAUSED

        print("Bot pausado")

    def resume(self):

        if self.state != BotState.PAUSED:
            return

        self.state = BotState.RUNNING

        print("Bot reanudado")

    # ==================================================
    # Game Loop
    # ==================================================

    def update(self):

        if self.state != BotState.RUNNING:
            return

        # Actualizar el estado del juego
        self.game_state_manager.update()

        # Obtener el estado actual
        state = self.game_state_manager.get_state()

        # Ejecutar módulos
        for module in self.modules:

            if module.is_enabled():

                module.update(state)

    # ==================================================
    # Consultas
    # ==================================================

    def is_running(self):

        return self.state == BotState.RUNNING

    def is_stopped(self):

        return self.state == BotState.STOPPED

    def is_paused(self):

        return self.state == BotState.PAUSED

    def get_state(self):

        return self.state

    def get_modules(self):

        return self.modules