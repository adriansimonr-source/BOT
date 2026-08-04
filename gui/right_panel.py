from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.auto_card import AutoCard
from gui.widgets.consumable_card import ConsumableCard


class RightPanel(QWidget):

    enemy_ignore_changed = Signal(str, bool)
    enemy_ignores_changed = Signal(object, bool)
    unique_targets_changed = Signal(object)

    def __init__(self):
        super().__init__()
        self._controls_locked = False
        self.create_widgets()
        self.create_layout()
        self.apply_style()
        self.connect_signals()

    def create_widgets(self):
        self.auto_target = AutoCard("Auto Target", "E", interval=250)
        self.auto_attack = AutoCard(
            "Auto Attack", "R", interval=250, show_interval=True
        )
        self.auto_loot = AutoCard(
            "Auto Loot", "F", interval=500, show_interval=True
        )

        self.auto_pot1 = ConsumableCard(
            "F8 (AutoPot1)", "F8", 40, 2000
        )
        self.auto_mp = ConsumableCard(
            "F9 (AutoMP)", "F9", 30, 2000
        )
        self.auto_heal = ConsumableCard(
            "F10 (AutoHeal)", "F10", 40, 2000
        )

        self.ignore_targets = QCheckBox("Ignorar objetivos")
        self.unique_targets_checkbox = QCheckBox("Atacar objetivos únicos")

        self.available_label = QLabel("Disponibles")
        self.ignored_label = QLabel("Ignorados")
        self.unique_targets_label = QLabel("Únicos")

        self.available_list = QListWidget()
        self.ignored_list = QListWidget()
        self.unique_targets_list = QListWidget()
        for list_widget in (
            self.available_list,
            self.ignored_list,
            self.unique_targets_list,
        ):
            list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )

        self.add_ignore_button = QPushButton(">")
        self.remove_ignore_button = QPushButton("<")
        self.add_unique_button = QPushButton("+")
        self.remove_unique_button = QPushButton("−")

        self.unique_targets_checkbox.setEnabled(False)

        for button in self._list_buttons():
            button.setFixedWidth(30)

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(3)

        main_layout.addWidget(self.auto_target)
        main_layout.addWidget(self.auto_attack)
        main_layout.addWidget(self.auto_loot)
        main_layout.addWidget(self.auto_pot1)
        main_layout.addWidget(self.auto_mp)
        main_layout.addWidget(self.auto_heal)

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.ignore_targets)
        options_layout.addWidget(self.unique_targets_checkbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(3)
        lists_layout.addLayout(
            self._create_list_column(self.available_label, self.available_list)
        )
        lists_layout.addLayout(
            self._create_button_column(
                self.add_ignore_button,
                self.remove_ignore_button,
            )
        )
        lists_layout.addLayout(
            self._create_list_column(self.ignored_label, self.ignored_list)
        )
        lists_layout.addLayout(
            self._create_button_column(
                self.add_unique_button,
                self.remove_unique_button,
            )
        )
        lists_layout.addLayout(
            self._create_list_column(
                self.unique_targets_label,
                self.unique_targets_list,
            )
        )
        main_layout.addLayout(lists_layout)

    @staticmethod
    def _create_list_column(label, list_widget):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.addWidget(label)
        layout.addWidget(list_widget)
        return layout

    @staticmethod
    def _create_button_column(*buttons):
        layout = QVBoxLayout()
        layout.addStretch()
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch()
        return layout

    def apply_style(self):
        button_style = """
        QPushButton {
            background-color: #173B6D;
            color: white;
            border-radius: 6px;
            border: none;
            padding: 3px;
        }
        QPushButton:hover { background-color: #28558F; }
        QPushButton:pressed { background-color: #102A4D; }
        """
        for button in self._list_buttons():
            button.setStyleSheet(button_style)

        option_style = "font-size: 10px;"
        self.ignore_targets.setStyleSheet(option_style)
        self.unique_targets_checkbox.setStyleSheet(option_style)

    def connect_signals(self):
        self.add_ignore_button.clicked.connect(self.move_to_ignored)
        self.remove_ignore_button.clicked.connect(self.move_to_available)
        self.add_unique_button.clicked.connect(self.add_unique_target)
        self.remove_unique_button.clicked.connect(self.remove_unique_target)

    def move_to_ignored(self):
        names = self._selected_names(self.available_list)
        if not names:
            return

        unique_changed = False
        for name in names:
            if not self._find_item(self.ignored_list, name):
                self.ignored_list.addItem(name)
            self._remove_item_by_name(self.available_list, name)
            unique_changed |= self._remove_unique_target_by_name(name)

        self._sort_list(self.ignored_list)
        if unique_changed:
            self._unique_targets_updated()
        self.enemy_ignores_changed.emit(names, True)
        for name in names:
            self.enemy_ignore_changed.emit(name, True)

    def move_to_available(self):
        names = self._selected_names(self.ignored_list)
        if not names:
            return

        for name in names:
            if not self._find_item(self.available_list, name):
                self.available_list.addItem(name)
            self._remove_item_by_name(self.ignored_list, name)

        self._sort_list(self.available_list)
        self.enemy_ignores_changed.emit(names, False)
        for name in names:
            self.enemy_ignore_changed.emit(name, False)

    def add_unique_target(self):
        names = self._selected_names(self.available_list)
        names.extend(self._selected_names(self.ignored_list))
        if not names:
            text, accepted = QInputDialog.getMultiLineText(
                self,
                "Agregar objetivos únicos",
                "Un objetivo por línea:",
                "",
            )
            if not accepted:
                return
            names = text.splitlines()

        added_names = []
        unignored_names = []
        for raw_name in names:
            name = self._canonical_display_name(raw_name)
            if not name or self._contains_unique_target(name):
                continue

            ignored_item = self._find_item(self.ignored_list, name)
            if ignored_item:
                self.ignored_list.takeItem(self.ignored_list.row(ignored_item))
                if not self._find_item(self.available_list, name):
                    self.available_list.addItem(name)
                unignored_names.append(name)

            self.unique_targets_list.addItem(name)
            added_names.append(name)

        if not added_names:
            return

        self._sort_list(self.available_list)
        self._sort_list(self.unique_targets_list)
        self._unique_targets_updated()
        if unignored_names:
            self.enemy_ignores_changed.emit(unignored_names, False)
        for name in unignored_names:
            self.enemy_ignore_changed.emit(name, False)

    def remove_unique_target(self):
        names = self._selected_names(self.unique_targets_list)
        if not names:
            return
        for name in names:
            self._remove_item_by_name(self.unique_targets_list, name)
        self._unique_targets_updated()

    def _contains_unique_target(self, name):
        normalized = name.strip().casefold()
        return any(
            self.unique_targets_list.item(index).text().casefold() == normalized
            for index in range(self.unique_targets_list.count())
        )

    def get_ignored_targets(self):
        return self._list_names(self.ignored_list)

    def get_unique_targets(self):
        return self._list_names(self.unique_targets_list)

    def set_enemy_names(self, enemy_names, ignored_names):
        canonical_names = {
            name.casefold(): name
            for name in enemy_names
            if name.strip()
        }
        ignored = {name.casefold() for name in ignored_names}
        available_names = sorted(
            (
                name
                for normalized, name in canonical_names.items()
                if normalized not in ignored
            ),
            key=str.casefold,
        )
        ignored_display_names = sorted(
            (
                canonical_names.get(normalized, name)
                for normalized, name in {
                    name.casefold(): name
                    for name in ignored_names
                }.items()
            ),
            key=str.casefold,
        )
        self._set_list_items(self.available_list, available_names)
        self._set_list_items(self.ignored_list, ignored_display_names)
        unique_changed = False
        for name in ignored_display_names:
            unique_changed |= self._remove_unique_target_by_name(name)
        if unique_changed:
            self._unique_targets_updated()

    @staticmethod
    def _set_list_items(list_widget, names):
        current_names = [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]
        if current_names == names:
            return
        list_widget.clear()
        list_widget.addItems(names)

    @staticmethod
    def _find_item(list_widget, name):
        normalized = name.strip().casefold()
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.text().casefold() == normalized:
                return item
        return None

    def _remove_unique_target_by_name(self, name):
        item = self._find_item(self.unique_targets_list, name)
        if item:
            self.unique_targets_list.takeItem(
                self.unique_targets_list.row(item)
            )
            return True
        return False

    @staticmethod
    def _selected_names(list_widget):
        return [item.text() for item in list_widget.selectedItems()]

    @staticmethod
    def _list_names(list_widget):
        return [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]

    @classmethod
    def _remove_item_by_name(cls, list_widget, name):
        item = cls._find_item(list_widget, name)
        if item:
            list_widget.takeItem(list_widget.row(item))

    def _canonical_display_name(self, name):
        name = str(name or "").strip()
        if not name:
            return ""
        for list_widget in (self.available_list, self.ignored_list):
            item = self._find_item(list_widget, name)
            if item:
                return item.text()
        return name

    @classmethod
    def _sort_list(cls, list_widget):
        names = sorted(cls._list_names(list_widget), key=str.casefold)
        cls._set_list_items(list_widget, names)

    def _unique_targets_updated(self):
        names = self.get_unique_targets()
        has_targets = bool(names)
        if not has_targets:
            self.unique_targets_checkbox.setChecked(False)
        self.unique_targets_checkbox.setEnabled(
            has_targets and not self._controls_locked
        )
        self.unique_targets_changed.emit(names)

    def lock_controls(self):
        self._controls_locked = True
        for card in self._cards():
            card.lock()
        for widget in self._target_widgets():
            widget.setEnabled(False)

    def unlock_controls(self):
        self._controls_locked = False
        for card in self._cards():
            card.unlock()
        for widget in self._target_widgets():
            widget.setEnabled(True)
        self.unique_targets_checkbox.setEnabled(
            self.unique_targets_list.count() > 0
        )

    def _cards(self):
        return (
            self.auto_target,
            self.auto_attack,
            self.auto_loot,
            self.auto_pot1,
            self.auto_mp,
            self.auto_heal,
        )

    def _target_widgets(self):
        return (
            self.ignore_targets,
            self.unique_targets_checkbox,
            self.available_list,
            self.ignored_list,
            self.unique_targets_list,
            *self._list_buttons(),
        )

    def _list_buttons(self):
        return (
            self.add_ignore_button,
            self.remove_ignore_button,
            self.add_unique_button,
            self.remove_unique_button,
        )
