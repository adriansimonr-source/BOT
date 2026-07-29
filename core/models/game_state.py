from core.models.player_state import PlayerState
from core.models.target_state import TargetState
from core.models.enemy_state import EnemyState


class GameState:

    def __init__(self):

        # =====================================
        # Conexión
        # =====================================

        self.connected = False


        # =====================================
        # Entidades
        # =====================================

        self.player = PlayerState()

        # Objetivo seleccionado actualmente

        self.target = TargetState()


        # Objetivos detectados por visión

        self.visible_targets = []



        # =====================================
        # Combate global
        # =====================================

        self.in_combat = False



        # =====================================
        # Buffs globales
        # =====================================

        self.buffs = []