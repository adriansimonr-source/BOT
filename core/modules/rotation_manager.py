import time
from dataclasses import dataclass

from core.modules.base_module import BaseModule


@dataclass
class SkillConfig:
    enabled: bool
    key: str
    cooldown: int
    last_cast: float = 0.0
    next_due: float | None = None


class RotationManager(BaseModule):
    SKILL_HOLD_MS = 25
    STANDARD_SKILL_KEYS = frozenset(str(number) for number in range(1, 10))
    PRIORITY_SKILL_KEYS = frozenset(f"F{number}" for number in range(1, 8))
    ALLOWED_SKILL_KEYS = STANDARD_SKILL_KEYS | PRIORITY_SKILL_KEYS

    def __init__(self, input_manager):
        super().__init__("Rotation Manager", interval_ms=25)
        self.input = input_manager
        self.skills: list[SkillConfig] = []
        self._tie_cursors = {False: 0, True: 0}

    def configure(self, right_panel, center_panel):
        self.skills = []
        for card in center_panel.skills:
            key = str(card.skill_number()).upper()
            if card.is_enabled() and key in self.ALLOWED_SKILL_KEYS:
                self.skills.append(SkillConfig(True, key, card.time()))
        self._tie_cursors = {False: 0, True: 0}

    def merge_config(self, skill_values, now_ms=None):
        if now_ms is None:
            now_ms = time.perf_counter() * 1000

        previous = {skill.key: skill for skill in self.skills}
        next_keys = {
            priority: self._next_key_for_group(priority)
            for priority in (False, True)
        }

        merged = []
        for value in skill_values:
            key = str(value.skill_number()).upper()
            if not value.is_enabled() or key not in self.ALLOWED_SKILL_KEYS:
                continue
            old = previous.get(key)
            cooldown = max(1, int(value.time()))
            last_cast = old.last_cast if old is not None else now_ms
            next_due = (
                old.next_due
                if old is not None and cooldown == old.cooldown
                else now_ms + cooldown
            )
            merged.append(
                SkillConfig(
                    True,
                    key,
                    cooldown,
                    last_cast,
                    next_due,
                )
            )

        self.skills = merged
        self._tie_cursors = {
            priority: next(
                (
                    index
                    for index, skill in enumerate(self.skills)
                    if skill.key == next_keys[priority]
                ),
                0,
            )
            for priority in (False, True)
        }

    def is_enabled(self):
        return bool(self.skills)

    def on_start(self):
        super().on_start()
        now = time.perf_counter() * 1000
        self._tie_cursors = {False: 0, True: 0}
        for skill in self.skills:
            skill.last_cast = now
            skill.next_due = now + skill.cooldown

    def on_stop(self):
        self._tie_cursors = {False: 0, True: 0}
        for skill in self.skills:
            skill.next_due = None

    def update(self, state):
        if not self.skills:
            return False

        now = time.perf_counter() * 1000
        skill_count = len(self.skills)
        due_skills = []
        for index, skill in enumerate(self.skills):
            skill.cooldown = max(1, int(skill.cooldown))
            due_at = (
                skill.next_due
                if skill.next_due is not None
                else skill.last_cast + skill.cooldown
            )
            if now < due_at:
                continue
            due_skills.append((index, skill, due_at))
            skill.next_due = self._next_period(due_at, skill.cooldown, now)

        if not due_skills:
            return False

        candidates = self._prioritize_candidates(due_skills, skill_count)

        index, skill, _ = candidates[0]
        delivered = self.input.press(
            skill.key,
            hold_ms=self.SKILL_HOLD_MS,
        )
        self._advance_tie_cursor(index, skill_count, skill.key)
        if not delivered:
            return False

        skill.last_cast = self._last_delivery_ms(skill.key, now)
        skill.next_due = skill.last_cast + skill.cooldown
        return True

    def _prioritize_candidates(self, candidates, skill_count):
        def scheduling_key(item):
            priority = self._is_priority_skill(item[1].key)
            return (
                item[2],
                (item[0] - self._tie_cursors[priority]) % skill_count,
            )

        priority = sorted(
            (
                item
                for item in candidates
                if self._is_priority_skill(item[1].key)
            ),
            key=scheduling_key,
        )
        standard = sorted(
            (
                item
                for item in candidates
                if not self._is_priority_skill(item[1].key)
            ),
            key=scheduling_key,
        )
        return priority + standard

    @classmethod
    def _is_priority_skill(cls, key):
        return str(key).upper() in cls.PRIORITY_SKILL_KEYS

    def _next_key_for_group(self, priority):
        if not self.skills:
            return None
        skill_count = len(self.skills)
        candidates = [
            (index, skill)
            for index, skill in enumerate(self.skills)
            if self._is_priority_skill(skill.key) is priority
        ]
        if not candidates:
            return None
        _, skill = min(
            candidates,
            key=lambda item: (
                item[0] - self._tie_cursors[priority]
            ) % skill_count,
        )
        return skill.key

    def _advance_tie_cursor(self, index, skill_count, key):
        priority = self._is_priority_skill(key)
        self._tie_cursors[priority] = (index + 1) % skill_count

    @staticmethod
    def _next_period(due_at, cooldown, now):
        periods = int((now - due_at) // cooldown) + 1
        return due_at + periods * cooldown

    def _last_delivery_ms(self, key, started_at):
        delivered_at = time.perf_counter() * 1000
        getter = getattr(self.input, "last_press_at", None)
        if not callable(getter):
            return delivered_at
        pressed_at = getter(key)
        if pressed_at is None:
            return delivered_at
        try:
            pressed_at_ms = float(pressed_at) * 1000
        except (TypeError, ValueError, OverflowError):
            return delivered_at
        if started_at <= pressed_at_ms <= delivered_at:
            return pressed_at_ms
        return delivered_at
