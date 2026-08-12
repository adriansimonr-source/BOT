import time


class PlayerState:

    POSITION_MAX_AGE_SECONDS = 3.0

    def __init__(self):
        self.hp_percent = 0
        self.mp_percent = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.position_valid = False
        self.position_updated_at = 0.0
        self.position_revision = 0
        self.start_x = 0
        self.start_y = 0
        self.position_locked = False

    def update_position(self, x, y):
        x = int(x)
        y = int(y)
        if not 10 <= x <= 999 or not 10 <= y <= 999:
            return False
        self.x = x
        self.y = y
        self.position_valid = True
        self.position_updated_at = time.perf_counter()
        self.position_revision += 1
        return True

    def has_fresh_position(self, max_age=None):
        if not self.position_valid:
            return False
        if max_age is None:
            max_age = self.POSITION_MAX_AGE_SECONDS
        return time.perf_counter() - self.position_updated_at <= max_age

    def invalidate_position(self):
        self.position_valid = False
        self.position_updated_at = 0.0

    def lock_position(self):
        if not self.has_fresh_position():
            return False
        self.start_x = self.x
        self.start_y = self.y
        self.position_locked = True
        return True

    def unlock_position(self):
        self.position_locked = False
        self.start_x = 0
        self.start_y = 0

    def reset(self):
        self.hp_percent = 0
        self.mp_percent = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.position_valid = False
        self.position_updated_at = 0.0
        self.position_revision = 0
        self.unlock_position()
