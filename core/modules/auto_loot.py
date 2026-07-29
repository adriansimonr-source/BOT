from core.modules.base_module import BaseModule


class AutoLoot(BaseModule):

    def __init__(self):
        super().__init__("Auto Loot")

    def update(self):

        if not self.is_enabled():
            return

        # Aquí irá la lógica del loot
        # print("AutoLoot")