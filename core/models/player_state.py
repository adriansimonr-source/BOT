import math
import time


class PlayerState:

    POSITION_MAX_AGE_SECONDS = 3.0
    RESOURCE_MAX_AGE_SECONDS = 0.75

    def __init__(self):
        self.hp_percent = 0
        self.hp_valid = False
        self.hp_updated_at = 0.0
        self.mp_percent = 0
        self.mp_valid = False
        self.mp_updated_at = 0.0
        self.x = 0
        self.y = 0
        self.z = 0
        self.position_valid = False
        self.position_updated_at = 0.0
        self.position_revision = 0
        self.position_history = []
        self.minimap_heading_deg = None
        self.minimap_heading_confidence = 0.0
        self.minimap_heading_valid = False
        self.minimap_heading_updated_at = 0.0
        self.minimap_heading_revision = 0
        self.start_x = 0
        self.start_y = 0
        self.position_locked = False

    @staticmethod
    def _normalize_resource(value, observed_at):
        if observed_at is None:
            observed_at = time.perf_counter()
        try:
            value = float(value)
            observed_at = float(observed_at)
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(value) or not math.isfinite(observed_at):
            return None
        if not 0.0 <= value <= 100.0:
            return None
        return value, observed_at

    def update_hp(self, value, observed_at=None):
        reading = self._normalize_resource(value, observed_at)
        if reading is None:
            self.hp_valid = False
            return False
        self.hp_percent, self.hp_updated_at = reading
        self.hp_valid = True
        return True

    def update_mp(self, value, observed_at=None):
        reading = self._normalize_resource(value, observed_at)
        if reading is None:
            self.mp_valid = False
            return False
        self.mp_percent, self.mp_updated_at = reading
        self.mp_valid = True
        return True

    @classmethod
    def resource_is_fresh(
        cls,
        player,
        resource,
        now=None,
        max_age=None,
    ):
        if not bool(getattr(player, f"{resource}_valid", False)):
            return False
        if now is None:
            now = time.perf_counter()
        if max_age is None:
            max_age = cls.RESOURCE_MAX_AGE_SECONDS
        try:
            updated_at = float(getattr(player, f"{resource}_updated_at"))
            age = float(now) - updated_at
            max_age = float(max_age)
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False
        return bool(
            math.isfinite(age)
            and math.isfinite(max_age)
            and max_age >= 0.0
            and age >= 0.0
            and age <= max_age
        )

    def has_fresh_hp(self, max_age=None, now=None):
        return self.resource_is_fresh(self, "hp", now=now, max_age=max_age)

    def has_fresh_mp(self, max_age=None, now=None):
        return self.resource_is_fresh(self, "mp", now=now, max_age=max_age)

    def invalidate_resources(self):
        self.hp_valid = False
        self.mp_valid = False

    def update_position(self, x, y, observed_at=None):
        x = int(x)
        y = int(y)
        if not 10 <= x <= 999 or not 10 <= y <= 999:
            return False
        if observed_at is None:
            observed_at = time.perf_counter()
        try:
            observed_at = float(observed_at)
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(observed_at):
            return False
        self.x = x
        self.y = y
        self.position_valid = True
        self.position_updated_at = observed_at
        self.position_revision += 1
        self.position_history.append(
            (
                self.position_revision,
                self.position_updated_at,
                self.x,
                self.y,
            )
        )
        if len(self.position_history) > 4:
            del self.position_history[:-4]
        return True

    def has_fresh_position(self, max_age=None):
        if not self.position_valid:
            return False
        if max_age is None:
            max_age = self.POSITION_MAX_AGE_SECONDS
        return time.perf_counter() - self.position_updated_at <= max_age

    def update_minimap_heading(self, angle, confidence, observed_at=None):
        if observed_at is None:
            observed_at = time.perf_counter()
        try:
            angle = float(angle) % 360.0
            confidence = min(1.0, max(0.0, float(confidence)))
            observed_at = float(observed_at)
        except (TypeError, ValueError, OverflowError):
            return False
        if not all(math.isfinite(value) for value in (angle, confidence, observed_at)):
            return False
        self.minimap_heading_deg = angle
        self.minimap_heading_confidence = confidence
        self.minimap_heading_valid = True
        self.minimap_heading_updated_at = observed_at
        self.minimap_heading_revision += 1
        return True

    def has_fresh_minimap_heading(self, max_age=0.5, min_confidence=0.55):
        return bool(
            self.minimap_heading_valid
            and self.minimap_heading_deg is not None
            and self.minimap_heading_confidence >= min_confidence
            and time.perf_counter() - self.minimap_heading_updated_at <= max_age
        )

    def invalidate_minimap_heading(self):
        self.minimap_heading_valid = False
        self.minimap_heading_updated_at = 0.0

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
        self.hp_valid = False
        self.hp_updated_at = 0.0
        self.mp_percent = 0
        self.mp_valid = False
        self.mp_updated_at = 0.0
        self.x = 0
        self.y = 0
        self.z = 0
        self.position_valid = False
        self.position_updated_at = 0.0
        self.position_revision = 0
        self.position_history = []
        self.minimap_heading_deg = None
        self.minimap_heading_confidence = 0.0
        self.minimap_heading_valid = False
        self.minimap_heading_updated_at = 0.0
        self.minimap_heading_revision = 0
        self.unlock_position()
