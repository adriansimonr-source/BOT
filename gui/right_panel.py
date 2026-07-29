from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QWidget, QPushButton
from gui.widgets.feature_card import FeatureCard

class RightPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.setMaximumWidth(350)
        self.create_widget()
        self.create_layout()

    def create_widget(self):

        self.automations_group = QGroupBox ("")

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
        self.Buff1 = FeatureCard(
            title="Buff1",
            default_key="F1",
            default_interval=500,
        )
        self.Buff2 = FeatureCard(
            title="Buff2",
            default_key="F2",
            default_interval=500,
        )
        self.Buff3 = FeatureCard(
            title="Buff3",
            default_key="F3",
            default_interval=500,
        )

    def create_layout(self):

        automations_layout = QVBoxLayout()

        automations_layout.addWidget(self.auto_target)
        automations_layout.addWidget(self.auto_attack)
        automations_layout.addWidget(self.auto_loot)
        automations_layout.addWidget(self.Buff1)
        automations_layout.addWidget(self.Buff2)
        automations_layout.addWidget(self.Buff3)

        self.automations_group.setLayout(automations_layout)


        main_layout = QVBoxLayout()

        main_layout.addWidget(self.automations_group)
        main_layout.addStretch()

        self.setLayout(main_layout)