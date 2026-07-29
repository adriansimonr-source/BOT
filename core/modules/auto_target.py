from core.modules.base_module import BaseModule


class AutoTarget(BaseModule):

    def __init__(self):
        super().__init__("Auto Target")

    def configure(self, right_panel, center_panel):

        self.set_interval(
            right_panel.auto_target.interval()
        )

        if right_panel.auto_target.is_enabled():
            self.enable()
        else:
            self.disable()

    def update(self, state):

        print(f"[Auto Target]: Tick ({self.interval_ms} ms)")