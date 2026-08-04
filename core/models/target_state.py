class TargetState:

    def __init__(self):
        self.selection_id = 0
        self.reset(clear_selection=False)

    def reset(self, clear_selection=True):
        self.exists = False
        self.name = ""
        self.level = 0
        self.hp_percent = 0.0
        self.visible = False
        self.targetable = False
        self.identity_pending = False
        self.auto_target_decision = None
        self.auto_target_decision_selection_id = None
        if clear_selection:
            self.selection_id = 0
