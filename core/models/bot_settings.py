from enum import Enum

class BotMode(Enum):

    STATIC_10 = 10

    STATIC_20 = 20

    STATIC_30 = 30

    STATIC_40 = 40

    OFF = -1

    STATIC_POINT = 0

class BotSettings:

    def __init__(self):

        self.mode = BotMode.STATIC_40

        self.auto_return = True

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
