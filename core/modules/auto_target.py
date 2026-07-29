from core.modules.base_module import BaseModule


class AutoTarget(BaseModule):

    def __init__(self):
        super().__init__("Auto Target")

    def update(self):

        if not self.is_enabled():
            return

        # Aquí irá la lógica de buscar objetivo
        # print("AutoTarget")