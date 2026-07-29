from core.modules.base_module import BaseModule


class BuffManager(BaseModule):

    def __init__(self):
        super().__init__("Buff Manager")

    def update(self):

        if not self.is_enabled():
            return

        # Aquí irá la lógica de buffs
        # print("BuffManager")