from core.modules.base_module import BaseModule


class AutoAttack(BaseModule):

    def __init__(self):
        super().__init__("Auto Attack")

    def configure(self, right_panel, center_panel):

        self.set_interval(
            right_panel.auto_attack.interval()
        )

        if right_panel.auto_attack.is_enabled():
            self.enable()
        else:
            self.disable()

    def update(self, state):

        print(f"[Auto Attack] Tick ({self.interval_ms} ms)")