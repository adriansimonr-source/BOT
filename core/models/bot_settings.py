from enum import Enum

class BotMode(Enum):

    STATIC_25 = 25

    STATIC_50 = 50

    STATIC_75 = 75

    STATIC_100 = 100

    OFF = -1

    STATIC_POINT = 0

class BotSettings:

    def __init__(self):

        self.mode = BotMode.STATIC_100

        self.auto_return = True

        self.return_delay = 10

        self.movement_hold_ms = 250

        self.returning = False

    def get_movement_range(self):

        if self.mode == BotMode.OFF:

            return None

        if self.mode == BotMode.STATIC_POINT:

            return 0

        return self.mode.value

    def set_mode(
        self,
        mode: BotMode
    ):

        self.mode = mode

    def set_return_delay(self, seconds):

        self.return_delay = max(3, int(seconds))
