from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QCheckBox,
)

from gui.widgets.auto_card import AutoCard
from gui.widgets.consumable_card import ConsumableCard



class RightPanel(QWidget):


    def __init__(self):

        super().__init__()

        self.create_widgets()
        self.create_layout()
        self.apply_style()
        self.connect_signals()



    def create_widgets(self):


        self.auto_target = AutoCard(
            "Auto Target",
            "E"
        )


        self.auto_attack = AutoCard(
            "Auto Attack",
            "R"
        )


        self.auto_loot = AutoCard(
            "Auto Loot",
            "F"
        )



        self.hp_potion = ConsumableCard(
            "F8 (AutoHP)",
            "F8",
            40,
            2000
        )


        self.mp_potion = ConsumableCard(
            "F9 (AutoMP)",
            "F9",
            30,
            2000
        )



        self.ignore_targets = QCheckBox(
            "Ignorar objetivos"
        )


        self.available_label = QLabel(
            "Disponibles"
        )


        self.ignored_label = QLabel(
            "Ignorados"
        )


        self.available_list = QListWidget()


        self.ignored_list = QListWidget()



        self.add_ignore_button = QPushButton(
            ">"
        )


        self.remove_ignore_button = QPushButton(
            "<"
        )


        self.add_ignore_button.setFixedWidth(
            35
        )


        self.remove_ignore_button.setFixedWidth(
            35
        )




    def create_layout(self):


        main_layout = QVBoxLayout(
            self
        )


        main_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )


        main_layout.setSpacing(
            6
        )



        auto_layout = QHBoxLayout()


        auto_layout.setSpacing(
            10
        )


        auto_layout.addWidget(
            self.auto_target
        )


        auto_layout.addWidget(
            self.auto_attack
        )


        auto_layout.addWidget(
            self.auto_loot
        )


        auto_layout.addStretch()



        main_layout.addLayout(
            auto_layout
        )



        main_layout.addWidget(
            self.hp_potion
        )


        main_layout.addWidget(
            self.mp_potion
        )



        main_layout.addWidget(
            self.ignore_targets
        )



        lists_layout = QHBoxLayout()



        available_layout = QVBoxLayout()


        available_layout.addWidget(
            self.available_label
        )


        available_layout.addWidget(
            self.available_list
        )



        buttons_layout = QVBoxLayout()


        buttons_layout.addStretch()


        buttons_layout.addWidget(
            self.add_ignore_button
        )


        buttons_layout.addWidget(
            self.remove_ignore_button
        )


        buttons_layout.addStretch()



        ignored_layout = QVBoxLayout()


        ignored_layout.addWidget(
            self.ignored_label
        )


        ignored_layout.addWidget(
            self.ignored_list
        )



        lists_layout.addLayout(
            available_layout
        )


        lists_layout.addLayout(
            buttons_layout
        )


        lists_layout.addLayout(
            ignored_layout
        )



        main_layout.addLayout(
            lists_layout
        )






    def apply_style(self):


        button_style = """

        QPushButton {

            background-color: #173B6D;

            color: white;

            border-radius: 6px;

            border: none;

            padding: 3px;

        }


        QPushButton:hover {

            background-color: #28558F;

        }


        QPushButton:pressed {

            background-color: #102A4D;

        }

        """



        for button in [
            self.add_ignore_button,
            self.remove_ignore_button,
        ]:

            button.setStyleSheet(
                button_style
            )






    def connect_signals(self):


        self.add_ignore_button.clicked.connect(
            self.move_to_ignored
        )


        self.remove_ignore_button.clicked.connect(
            self.move_to_available
        )






    def move_to_ignored(self):


        item = self.available_list.currentItem()


        if item:

            self.ignored_list.addItem(
                item.text()
            )


            self.available_list.takeItem(
                self.available_list.row(item)
            )






    def move_to_available(self):


        item = self.ignored_list.currentItem()


        if item:

            self.available_list.addItem(
                item.text()
            )


            self.ignored_list.takeItem(
                self.ignored_list.row(item)
            )






    def lock_controls(self):


        self.auto_target.lock()

        self.auto_attack.lock()

        self.auto_loot.lock()


        self.hp_potion.lock()

        self.mp_potion.lock()


        self.ignore_targets.setEnabled(
            False
        )


        self.available_list.setEnabled(
            False
        )


        self.ignored_list.setEnabled(
            False
        )






    def unlock_controls(self):


        self.auto_target.unlock()

        self.auto_attack.unlock()

        self.auto_loot.unlock()


        self.hp_potion.unlock()

        self.mp_potion.unlock()


        self.ignore_targets.setEnabled(
            True
        )


        self.available_list.setEnabled(
            True
        )


        self.ignored_list.setEnabled(
            True
        )