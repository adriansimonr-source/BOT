from core.models.game_state import GameState


class GameStateManager:

    def __init__(self, process_manager):

        self.process_manager = process_manager

        self.state = GameState()


    # =====================================
    # Actualización del estado
    # =====================================

    def update(self):

        if self.process_manager.is_connected():

            self.state.connected = True

        else:

            self.state.connected = False
            return


        # =====================================
        # Datos temporales del jugador
        # (más adelante vendrán del lector)
        # =====================================

        player = self.state.player

        player.name = "Davion"

        player.level = 1

        player.hp = 2500
        player.max_hp = 3000

        player.mp = 800
        player.max_mp = 1000

        player.x = 125
        player.y = 340


        # =====================================
        # Datos temporales del objetivo
        # =====================================

        target = self.state.target

        target.exists = True

        target.name = "Goblin Guerrero"

        target.level = 25

        target.hp = 500
        target.max_hp = 1000



    # =====================================
    # Acceso
    # =====================================

    def get_state(self):

        return self.state