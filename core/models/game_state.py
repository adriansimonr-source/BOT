from dataclasses import dataclass, field
from typing import List


@dataclass
class GameState:

    # ===========================
    # Personaje
    # ===========================

    hp: int = 0
    max_hp: int = 0

    mp: int = 0
    max_mp: int = 0

    level: int = 0

    # ===========================
    # Objetivo
    # ===========================

    target_exists: bool = False

    target_hp: int = 0
    target_max_hp: int = 0

    target_name: str = ""

    # ===========================
    # Posición
    # ===========================

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # ===========================
    # Estado
    # ===========================

    in_combat: bool = False

    dead: bool = False

    casting: bool = False

    moving: bool = False

    # ===========================
    # Buffs
    # ===========================

    buffs: List[str] = field(default_factory=list)

    # ===========================
    # Propiedades calculadas
    # ===========================

    @property
    def hp_percent(self):

        if self.max_hp == 0:
            return 0

        return int(self.hp / self.max_hp * 100)

    @property
    def mp_percent(self):

        if self.max_mp == 0:
            return 0

        return int(self.mp / self.max_mp * 100)

    @property
    def target_hp_percent(self):

        if self.target_max_hp == 0:
            return 0

        return int(self.target_hp / self.target_max_hp * 100)