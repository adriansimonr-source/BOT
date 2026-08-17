from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.auto_card import AutoCard
from gui.widgets.consumable_card import ConsumableCard


class RightPanel(QWidget):
    enemy_ignores_changed = Signal(object, bool)
    target_filters_save_requested = Signal()

    def __init__(self):
        super().__init__()
        self._target_filters_dirty = False
        self.create_widgets()
        self.create_layout()
        self.apply_style()
        self.connect_signals()

    def create_widgets(self):
        self.auto_target = AutoCard(
            "Target",
            "E",
            interval=10000,
            show_interval=True,
        )
        self.auto_target.interval_spin.setMinimum(4000)
        self.auto_target.interval_spin.setSingleStep(500)
        self.auto_target.interval_spin.setToolTip(
            "Tiempo máximo sin detectar una nueva bajada de vida antes de "
            "pulsar E."
        )
        self.auto_attack = AutoCard(
            "Attack", "R", interval=250, show_interval=True
        )
        self.auto_loot = AutoCard(
            "Loot", "F", interval=500, show_interval=True
        )
        self.auto_pot1 = ConsumableCard("F8 Pot1", "F8", 40, 2000)
        self.auto_mp = ConsumableCard("F9 MP", "F9", 30, 2000)
        self.auto_heal = ConsumableCard("F10 Heal", "F10", 40, 2000)

        self.ignore_targets = QCheckBox("Ignorar objetivos")
        self.ignore_targets.setToolTip(
            "AutoTarget cambiará los objetivos incluidos en Ignorados."
        )

        self.available_label = QLabel("Disponibles")
        self.ignored_label = QLabel("Ignorados")
        self.available_list = QListWidget()
        self.ignored_list = QListWidget()
        self.available_list.setToolTip(
            "Objetivos detectados que AutoTarget puede seleccionar."
        )
        self.ignored_list.setToolTip(
            "Objetivos que AutoTarget descartará al activar el filtro."
        )
        for list_widget in (self.available_list, self.ignored_list):
            list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )
            list_widget.setFixedSize(92, 46)

        self.add_ignore_button = QPushButton("→")
        self.add_ignore_button.setToolTip(
            "Mueve los objetivos seleccionados a Ignorados."
        )
        self.remove_ignore_button = QPushButton("←")
        self.remove_ignore_button.setToolTip(
            "Devuelve los objetivos seleccionados a Disponibles."
        )
        for button in (self.add_ignore_button, self.remove_ignore_button):
            button.setFixedSize(22, 20)

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(1)

        main_layout.addWidget(self.auto_target)
        main_layout.addWidget(self.auto_attack)
        main_layout.addWidget(self.auto_loot)
        main_layout.addWidget(self.auto_pot1)
        main_layout.addWidget(self.auto_mp)
        main_layout.addWidget(self.auto_heal)
        main_layout.addWidget(self.ignore_targets)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(3)
        lists_layout.addLayout(
            self._create_list_column(self.available_label, self.available_list),
            1,
        )

        arrows_layout = QVBoxLayout()
        arrows_layout.setSpacing(2)
        arrows_layout.addStretch()
        arrows_layout.addWidget(self.add_ignore_button)
        arrows_layout.addWidget(self.remove_ignore_button)
        arrows_layout.addStretch()
        lists_layout.addLayout(arrows_layout)

        lists_layout.addLayout(
            self._create_list_column(self.ignored_label, self.ignored_list),
            1,
        )
        main_layout.addLayout(lists_layout)

    @staticmethod
    def _create_list_column(label, list_widget):
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.addWidget(label)
        layout.addWidget(list_widget)
        return layout

    def apply_style(self):
        button_style = """
        QPushButton {
            background-color: #173B6D;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 1px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #28558F; }
        QPushButton:pressed { background-color: #102A4D; }
        QPushButton:disabled { background-color: #9CA9B8; }
        """
        for button in self._target_buttons():
            button.setStyleSheet(button_style)
        self.ignore_targets.setStyleSheet("font-size: 10px;")
        self.available_label.setStyleSheet("font-size: 10px;")
        self.ignored_label.setStyleSheet("font-size: 10px;")

    def connect_signals(self):
        self.add_ignore_button.clicked.connect(self.move_to_ignored)
        self.remove_ignore_button.clicked.connect(self.move_to_available)
        self.ignore_targets.stateChanged.connect(
            self._ignore_filter_changed
        )

    def move_to_ignored(self):
        names = self._selected_names(self.available_list)
        if not names:
            return
        for name in names:
            self._remove_item_by_name(self.available_list, name)
            if not self._find_item(self.ignored_list, name):
                self.ignored_list.addItem(name)
        self._sort_list(self.ignored_list)
        self.enemy_ignores_changed.emit(names, True)

    def move_to_available(self):
        names = self._selected_names(self.ignored_list)
        if not names:
            return
        for name in names:
            self._remove_item_by_name(self.ignored_list, name)
            if not self._find_item(self.available_list, name):
                self.available_list.addItem(name)
        self._sort_list(self.available_list)
        self.enemy_ignores_changed.emit(names, False)

    def set_enemy_names(self, enemy_names, ignored_names):
        canonical_names = {
            str(name).strip().casefold(): str(name).strip()
            for name in (*enemy_names, *ignored_names)
            if str(name).strip()
        }
        ignored_keys = {
            str(name).strip().casefold()
            for name in ignored_names
            if str(name).strip()
        }
        available_names = sorted(
            (
                name
                for key, name in canonical_names.items()
                if key not in ignored_keys
            ),
            key=str.casefold,
        )
        ignored_display_names = sorted(
            (
                canonical_names[key]
                for key in ignored_keys
                if key in canonical_names
            ),
            key=str.casefold,
        )
        self._set_list_items(self.available_list, available_names)
        self._set_list_items(self.ignored_list, ignored_display_names)

    def set_target_filters(self, ignore_enabled=False):
        blocker = QSignalBlocker(self.ignore_targets)
        self.ignore_targets.setChecked(bool(ignore_enabled))
        del blocker
        self.mark_target_filters_saved()

    def get_ignored_targets(self):
        return self._list_names(self.ignored_list)

    def get_target_filter_state(self):
        return {"ignore_enabled": self.ignore_targets.isChecked()}

    def has_unsaved_target_filters(self):
        return self._target_filters_dirty

    def mark_target_filters_saved(self):
        self._target_filters_dirty = False

    def _ignore_filter_changed(self, _value=None):
        self._target_filters_dirty = True
        self.target_filters_save_requested.emit()

    @staticmethod
    def _selected_names(list_widget):
        return [item.text() for item in list_widget.selectedItems()]

    @staticmethod
    def _list_names(list_widget):
        return [
            list_widget.item(index).text()
            for index in range(list_widget.count())
        ]

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
        normalized = str(name or "").strip().casefold()
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.text().casefold() == normalized:
                return item
        return None

    @classmethod
    def _remove_item_by_name(cls, list_widget, name):
        item = cls._find_item(list_widget, name)
        if not item:
            return False
        list_widget.takeItem(list_widget.row(item))
        return True

    @classmethod
    def _sort_list(cls, list_widget):
        cls._set_list_items(
            list_widget,
            sorted(cls._list_names(list_widget), key=str.casefold),
        )

    def lock_controls(self):
        for card in self._cards():
            card.lock()
        for widget in self._target_widgets():
            widget.setEnabled(False)

    def unlock_controls(self):
        for card in self._cards():
            card.unlock()
        for widget in self._target_widgets():
            widget.setEnabled(True)

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
            self.available_list,
            self.ignored_list,
            *self._target_buttons(),
        )

    def _target_buttons(self):
        return self.add_ignore_button, self.remove_ignore_button
