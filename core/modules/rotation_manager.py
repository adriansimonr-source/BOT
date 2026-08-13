import time
from dataclasses import dataclass

from core.modules.base_module import BaseModule


@dataclass
class SkillConfig:
    enabled: bool
    key: str
    cooldown: int
    last_cast: float = 0.0


@dataclass
class BufferedSkill:
    index: int
    due_at: float
    expires_at: float


class RotationManager(BaseModule):
    SKILL_HOLD_MS = 25
    SKILL_BUFFER_TTL_MS = 150
    MAX_SEND_ATTEMPTS_PER_TICK = 2

    def __init__(self, input_manager):
        super().__init__("Rotation Manager", interval_ms=25)
        self.input = input_manager
        self.skills: list[SkillConfig] = []
        self._tie_cursor = 0
        self._pending_skills: dict[str, BufferedSkill] = {}
        self._deferred_until: dict[str, float] = {}
        self._schedule_started = False

    def configure(self, right_panel, center_panel):
        self.skills = [
            SkillConfig(True, card.skill_number(), card.time())
            for card in center_panel.skills
            if card.is_enabled()
        ]
        self._pending_skills.clear()
        self._deferred_until.clear()

    def merge_config(self, skill_values, now_ms=None):
        if now_ms is None:
            now_ms = time.perf_counter() * 1000

        previous = {skill.key: skill for skill in self.skills}
        next_key = None
        if self.skills:
            next_key = self.skills[self._tie_cursor % len(self.skills)].key

        merged = []
        rearmed = {}
        for value in skill_values:
            if not value.is_enabled():
                continue
            key = str(value.skill_number())
            old = previous.get(key)
            cooldown = max(1, int(value.time()))
            merged.append(
                SkillConfig(
                    True,
                    key,
                    cooldown,
                    old.last_cast if old is not None else now_ms,
                )
            )
            if (
                old is not None
                and cooldown != old.cooldown
                and old.last_cast + cooldown <= now_ms
            ):
                rearmed[key] = now_ms

        self.skills = merged
        self._pending_skills.clear()
        self._deferred_until.clear()
        self._deferred_until.update(rearmed)
        if next_key is None:
            self._tie_cursor = 0
            return
        self._tie_cursor = next(
            (
                index
                for index, skill in enumerate(self.skills)
                if skill.key == next_key
            ),
            0,
        )

    def is_enabled(self):
        return bool(self.skills)

    def on_start(self):
        super().on_start()
        now = time.perf_counter() * 1000
        self._schedule_started = True
        self._tie_cursor = 0
        self._pending_skills.clear()
        self._deferred_until.clear()
        for skill in self.skills:
            skill.last_cast = now

    def on_stop(self):
        self._schedule_started = False
        self._pending_skills.clear()
        self._deferred_until.clear()

    def update(self, state):
        if not self.skills:
            return False

        now = time.perf_counter() * 1000
        skill_count = len(self.skills)
        due_skills = []
        for index, skill in enumerate(self.skills):
            buffered = self._pending_skills.get(skill.key)
            due_at = (
                buffered.due_at
                if buffered is not None
                else self._deferred_until.get(
                    skill.key,
                    skill.last_cast + skill.cooldown,
                )
            )
            if now < due_at:
                continue
            if buffered is not None and now >= buffered.expires_at:
                self._pending_skills.pop(skill.key, None)
                self._defer_until_next_period(skill, due_at, now)
                continue
            if (
                buffered is None
                and
                self._schedule_started
                and now >= due_at + self.SKILL_BUFFER_TTL_MS
            ):
                self._defer_until_next_period(skill, due_at, now)
                continue
            if self._coalesce_recent_press(skill, due_at, now, index):
                continue
            due_skills.append((index, skill, due_at))

        if not due_skills:
            return False

        for index, skill, due_at in due_skills:
            if skill.key not in self._pending_skills:
                self._pending_skills[skill.key] = BufferedSkill(
                    index=index,
                    due_at=due_at,
                    expires_at=(
                        due_at + self.SKILL_BUFFER_TTL_MS
                        if self._schedule_started
                        else now + self.SKILL_BUFFER_TTL_MS
                    ),
                )

        candidates = [
            (buffered.index, self.skills[buffered.index], buffered)
            for buffered in self._pending_skills.values()
            if buffered.index < skill_count
        ]
        candidates.sort(
            key=lambda item: (
                item[1].cooldown,
                item[2].due_at,
                (item[0] - self._tie_cursor) % skill_count,
            ),
        )

        attempts = 0
        for index, skill, _ in candidates:
            if attempts >= self.MAX_SEND_ATTEMPTS_PER_TICK:
                break
            attempts += 1
            if self.input.press(skill.key, hold_ms=self.SKILL_HOLD_MS):
                skill.last_cast = now
                self._pending_skills.pop(skill.key, None)
                self._deferred_until.pop(skill.key, None)
                self._tie_cursor = (index + 1) % skill_count
                return True
            self._tie_cursor = (index + 1) % skill_count
        return False

    def _coalesce_recent_press(self, skill, due_at, now, index):
        getter = getattr(self.input, "last_press_at", None)
        if not callable(getter):
            return False
        pressed_at = getter(skill.key)
        if pressed_at is None:
            return False
        pressed_at_ms = pressed_at * 1000
        if not due_at <= pressed_at_ms <= now:
            return False
        if now - pressed_at_ms > self.SKILL_BUFFER_TTL_MS:
            return False
        skill.last_cast = pressed_at_ms
        self._pending_skills.pop(skill.key, None)
        self._deferred_until.pop(skill.key, None)
        self._tie_cursor = (index + 1) % len(self.skills)
        return True

    def _defer_until_next_period(self, skill, due_at, now):
        next_due = due_at + skill.cooldown
        if next_due <= now:
            missed = int((now - next_due) // skill.cooldown) + 1
            next_due += missed * skill.cooldown
        self._deferred_until[skill.key] = next_due
