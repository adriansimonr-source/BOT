import time
from dataclasses import dataclass

from core.modules.base_module import BaseModule


@dataclass
class SkillConfig:
    enabled: bool
    key: str
    cooldown: int
    last_cast: float = 0.0


class RotationManager(BaseModule):
    SKILL_HOLD_MS = 25

    def __init__(self, input_manager):
        super().__init__("Rotation Manager", interval_ms=25)
        self.input = input_manager
        self.skills: list[SkillConfig] = []
        self._tie_cursor = 0

    def configure(self, right_panel, center_panel):
        self.skills = [
            SkillConfig(True, card.skill_number(), card.time())
            for card in center_panel.skills
            if card.is_enabled()
        ]

    def is_enabled(self):
        return bool(self.skills)

    def on_start(self):
        super().on_start()
        now = time.perf_counter() * 1000
        self._tie_cursor = 0
        for skill in self.skills:
            skill.last_cast = now

    def update(self, state):
        if not self.skills:
            return False

        now = time.perf_counter() * 1000
        skill_count = len(self.skills)
        due_skills = [
            (index, skill)
            for index, skill in enumerate(self.skills)
            if now >= skill.last_cast + skill.cooldown
        ]

        if not due_skills:
            return False

        index, skill = min(
            due_skills,
            key=lambda item: (
                item[1].cooldown,
                item[1].last_cast + item[1].cooldown,
                (item[0] - self._tie_cursor) % skill_count,
            ),
        )

        if self.input.press(skill.key, hold_ms=self.SKILL_HOLD_MS):
            skill.last_cast = now
            self._tie_cursor = (index + 1) % skill_count
            return True
        return False
