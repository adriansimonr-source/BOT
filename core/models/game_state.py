from core.models.player_state import PlayerState
from core.models.target_state import TargetState
from core.models.enemy_state import EnemyState


class GameState:


    def __init__(self):

        # =====================================

        self.connected = False


        # Jugador actual

        self.player = PlayerState()


        # Objetivo seleccionado actualmente

        self.target = TargetState()

        # Enemigos detectados por visión

        self.visible_targets: list[EnemyState] = []


        self.in_combat = False
        self.buffs = []


    def reset(self):


        self.connected = False
        self.player.reset()
        self.target.reset()
        self.visible_targets.clear()
        self.in_combat = False
        self.buffs.clear()