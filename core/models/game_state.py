from core.models.player_state import PlayerState
from core.models.target_state import TargetState


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

        self.target = TargetState()


        # =====================================
        # Combate global
        # =====================================

        self.in_combat = False


        # =====================================
        # Buffs globales
        # =====================================

        self.buffs = []