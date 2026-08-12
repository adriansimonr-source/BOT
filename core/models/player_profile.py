from core.models.bot_settings import BotSettings
from core.models.target_rules import TargetRules


class PlayerProfile:
    def __init__(self):
        self.bot_settings = BotSettings()
        self.target_rules = TargetRules()
