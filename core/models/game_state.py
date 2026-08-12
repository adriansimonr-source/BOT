from core.models.player_state import PlayerState
from core.models.target_state import TargetState

class GameState:

    def __init__(self):

        self.connected = False

        self.player = PlayerState()

        self.target = TargetState()

        self.in_combat = False

        self.navigation_active = False
        self.navigation_status = "idle"
        self.navigation_reason = ""
        self.navigation_distance = None
        self.navigation_key = None

    def reset(self):

        self.connected = False
        self.player.reset()
        self.target.reset()
        self.in_combat = False
        self.navigation_active = False
        self.navigation_status = "idle"
        self.navigation_reason = ""
        self.navigation_distance = None
        self.navigation_key = None
