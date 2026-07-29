from core.models.bot_settings import BotSettings
from core.models.target_rules import TargetRules


class PlayerProfile:


    def __init__(self, name=""):


        # =====================================
        # Identidad
        # =====================================

        self.name = name



        # =====================================
        # Configuración del bot
        # =====================================

        self.bot_settings = BotSettings()



        # =====================================
        # Reglas de objetivos
        # =====================================

        self.target_rules = TargetRules()



        # =====================================
        # Rotación
        # =====================================

        # Más adelante:
        # skills activas
        # cooldowns
        # prioridades

        self.rotation = []



    # =====================================
    # Nombre
    # =====================================

    def set_name(
        self,
        name: str
    ):

        self.name = name