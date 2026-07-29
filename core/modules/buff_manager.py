import time
from dataclasses import dataclass

from core.modules.base_module import BaseModule


@dataclass
class BuffConfig:
    enabled: bool
    key: str
    interval: int
    last_cast: float = 0.0


class BuffManager(BaseModule):

    def __init__(self):

        super().__init__("Buff Manager")

        self.buffs: list[BuffConfig] = []


    def configure(self, right_panel, center_panel):

        self.buffs.clear()

        cards = [
            right_panel.buff1,
            right_panel.buff2,
            right_panel.buff3,
        ]

        for card in cards:

            self.buffs.append(

                BuffConfig(
                    enabled=card.is_enabled(),
                    key=card.key(),
                    interval=card.interval(),
                )

            )

# Game Loop

    def update(self, state):

        now = time.perf_counter() * 1000

        for buff in self.buffs:

            if not buff.enabled:
                continue

            if (now - buff.last_cast) < buff.interval:
                continue

            buff.last_cast = now

            print(f"Buff -> {buff.key} (interval: {buff.interval} ms)")