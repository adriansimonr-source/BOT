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

        automations_layout.setContentsMargins(5, 5, 5, 5)
        automations_layout.setHorizontalSpacing(10)
        automations_layout.setVerticalSpacing(10)

        automations_layout.addWidget(self.auto_target, 0, 0)
        automations_layout.addWidget(self.auto_attack, 0, 1)
        automations_layout.addWidget(self.auto_loot, 0, 2)

        automations_layout.addWidget(self.buff1, 1, 0)
        automations_layout.addWidget(self.buff2, 1, 1)
        automations_layout.addWidget(self.buff3, 1, 2)

        self.automations_group.setLayout(automations_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.automations_group)
        main_layout.addStretch()

        self.setLayout(main_layout)