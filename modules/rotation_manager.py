from core.modules.base_module import BaseModule


class RotationManager(BaseModule):

    def __init__(self):
        super().__init__("Rotation Manager")

    def update(self):

        if not self.is_enabled():
            return

        # Aquí irá la lógica de la rotación
        # print("RotationManager")