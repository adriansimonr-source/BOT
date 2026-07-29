from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QGridLayout,
)

from gui.widgets.feature_card import FeatureCard


class RightPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):

        self.automations_group = QGroupBox("AUTO")

        self.auto_target = FeatureCard(
            title="Auto Target",
            default_key="E",
            default_interval=500,
        )

        self.auto_attack = FeatureCard(
            title="Auto Attack",
            default_key="R",
            default_interval=500,
        )

        self.auto_loot = FeatureCard(
            title="Auto Loot",
            default_key="F",
            default_interval=500,
        )

        self.buff1 = FeatureCard(
            title="Buff 1",
            default_key="F1",
            default_interval=500,
        )

        self.buff2 = FeatureCard(
            title="Buff 2",
            default_key="F2",
            default_interval=500,
        )

        self.buff3 = FeatureCard(
            title="Buff 3",
            default_key="F3",
            default_interval=500,
        )

    def create_layout(self):

        automations_layout = QGridLayout()

        automations_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        automations_layout.setHorizontalSpacing(10)
        automations_layout.setVerticalSpacing(10)

        # Primera fila
        automations_layout.addWidget(
            self.auto_target,
            0,
            0
        )

        automations_layout.addWidget(
            self.auto_attack,
            0,
            1
        )

        automations_layout.addWidget(
            self.auto_loot,
            0,
            2
        )

        # Segunda fila
        automations_layout.addWidget(
            self.buff1,
            1,
            0
        )

        automations_layout.addWidget(
            self.buff2,
            1,
            1
        )

        automations_layout.addWidget(
            self.buff3,
            1,
            2
        )

        self.automations_group.setLayout(
            automations_layout
        )

        main_layout = QVBoxLayout()

        main_layout.addWidget(
            self.automations_group
        )

        main_layout.addStretch()

        self.setLayout(
            main_layout
        )

    # Bloqueo/desbloqueo de configuración

    def lock_controls(self):

        self.auto_target.lock()
        self.auto_attack.lock()
        self.auto_loot.lock()

        self.buff1.lock()
        self.buff2.lock()
        self.buff3.lock()


    def unlock_controls(self):

        self.auto_target.unlock()
        self.auto_attack.unlock()
        self.auto_loot.unlock()

        self.buff1.unlock()
        self.buff2.unlock()
        self.buff3.unlock()