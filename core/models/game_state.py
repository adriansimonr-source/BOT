from core.models.player_state import PlayerState
from core.models.target_state import TargetState

class GameState:

    def __init__(self):

        # =====================================
        # Conexión
        # =====================================

        self.connected = False

        self.player = PlayerState()

        self.target = TargetState()
        # =====================================
        # Personaje
        # =====================================

        self.character_name = ""

        self.level = 0


        # =====================================
        # Estadísticas
        # =====================================

        self.hp = 0
        self.max_hp = 0

        self.mp = 0
        self.max_mp = 0


        # =====================================
        # Posición
        # =====================================

        self.x = 0
        self.y = 0


        # =====================================
        # Combate
        # =====================================

        self.in_combat = False
        self.has_target = False


        # =====================================
        # Buffs
        # =====================================

        self.buffs = []


    # =====================================
    # Helpers
    # =====================================

    def hp_percentage(self):

        if self.max_hp <= 0:
            return 0

        return int(
            (self.hp / self.max_hp) * 100
        )