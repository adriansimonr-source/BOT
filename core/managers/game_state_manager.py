from core.models.game_state import GameState


class GameStateManager:

    def __init__(self):

        self.state = GameState()

    def update(self):

        """
        Aquí en el futuro leeremos la información del juego.

        De momento solo dejamos preparado el método.
        """

        pass

    def get_state(self):

        return self.state