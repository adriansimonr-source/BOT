from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)

from gui.widgets.resource_bar import ResourceBar

class TargetGroup(QWidget):

    def __init__(self):

        super().__init__()

        self.create_widgets()

        self.create_layout()

    def create_widgets(self):

        self.target_name_label = QLabel(

            "TARGET: ---"

        )

        self.level_label = QLabel(

            "LVL: -"

        )

        self.hp_bar = ResourceBar(

            "HP"

        )

        self.hp_bar.setFixedWidth(140)

    def create_layout(self):

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(

            2,

            2,

            2,

            2

        )

        main_layout.setSpacing(

            4

        )

        main_layout.addWidget(self.target_name_label)

        main_layout.addWidget(self.level_label)

        main_layout.addWidget(

            self.hp_bar

        )

        main_layout.addStretch()

        self.setLayout(

            main_layout

        )

    def update_state(

        self,

        state

    ):

        target = state.target

        if not target.exists:

            self.target_name_label.setText(

                "TARGET: ---"

            )

            self.level_label.setText(

                "LVL: -"

            )

            self.hp_bar.update_percent(

                0

            )

            return

        self.target_name_label.setText(

            f"TARGET: {target.name}"

            if target.name

            else

            "TARGET: ---"

        )

        self.level_label.setText(

            f"LVL: {target.level}"

        )

        self.hp_bar.update_percent(

            target.hp_percent if target.hp_valid else None

        )
