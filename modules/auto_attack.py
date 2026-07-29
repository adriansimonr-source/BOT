from core.modules.base_module import BaseModule


class AutoAttack(BaseModule):

    def __init__(self):
        super().__init__("Auto Attack")

    def update(self):

        if not self.is_enabled():
            return

        # Aquí irá la lógica del ataque
        # print("AutoAttack")