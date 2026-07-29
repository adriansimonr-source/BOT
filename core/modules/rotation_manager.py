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

    def __init__(self):

        super().__init__("Rotation Manager")

        self.skills: list[SkillConfig] = []

    def configure(self, right_panel, center_panel):

        self.skills.clear()

        for skill_card in center_panel.skills:

            self.skills.append(
                SkillConfig(
                    enabled=skill_card.is_enabled(),
                    key=skill_card.skill_number(),
                    cooldown=skill_card.time()
                )
            )

    # Game Loop

    def update(self, state):

        now = time.perf_counter() * 1000

        for skill in self.skills:

            if not skill.enabled:
                continue

            if (now - skill.last_cast) < skill.cooldown:
                continue

            skill.last_cast = now

            print(
                f"[Rotation] Ejecutando skill {skill.key} (cooldown: {skill.cooldown} ms)"
            )

            break