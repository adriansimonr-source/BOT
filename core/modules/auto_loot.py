from core.modules.base_module import BaseModule


class AutoLoot(BaseModule):

    def __init__(self):
        super().__init__("Auto Loot")

    def configure(self, right_panel, center_panel):

        self.set_interval(
            right_panel.auto_loot.interval()
        )

        if right_panel.auto_loot.is_enabled():
            self.enable()
        else:
            self.disable()

    def update(self, state):

        print(f"[Auto Loot] Tick ({self.interval_ms} ms)")