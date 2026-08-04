from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
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
    target_filters_save_requested = Signal()

    def __init__(self):
        super().__init__()
        self._controls_locked = False
        self._target_filters_dirty = False
        self._database_enemy_names = []
        self.create_widgets()
        self.create_layout()
        self.apply_style()
        self.connect_signals()
        self._refresh_available_combo()

    def create_widgets(self):
        self.auto_target = AutoCard("Auto Target", "E", interval=250)
        self.auto_attack = AutoCard(
            "Auto Attack", "R", interval=250, show_interval=True
        )
        self.auto_loot = AutoCard(
            "Auto Loot", "F", interval=500, show_interval=True
        )
        self.auto_pot1 = ConsumableCard("F8 (AutoPot1)", "F8", 40, 2000)
        self.auto_mp = ConsumableCard("F9 (AutoMP)", "F9", 30, 2000)
        self.auto_heal = ConsumableCard("F10 (AutoHeal)", "F10", 40, 2000)

        self.ignore_targets = QCheckBox("Ignorar objetivos")
        self.unique_targets_checkbox = QCheckBox("Atacar objetivos únicos")
        self.ignore_targets.setToolTip(
            "AutoTarget cambiará cualquier objetivo incluido en Ignorados."
        )
        self.unique_targets_checkbox.setToolTip(
            "AutoTarget buscará solo estos nombres y mantendrá "
            "el objetivo hasta que desaparezca."
        )
        self.unique_targets_checkbox.setEnabled(False)

        self.available_label = QLabel("Disponibles")
        self.ignored_label = QLabel("Ignorados")
        self.unique_targets_label = QLabel("Únicos")

        self.available_combo = QComboBox()
        self.available_combo.setToolTip(
            "Enemigos detectados y validados en la base de datos."
        )
        self.available_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.available_combo.setMinimumContentsLength(10)
        self.available_combo.setFixedHeight(24)

        self.ignored_list = QListWidget()
        self.unique_targets_list = QListWidget()
        for list_widget in (self.ignored_list, self.unique_targets_list):
            list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )

        self.add_ignore_button = QPushButton("A Ignorados")
        self.add_unique_button = QPushButton("A Únicos")
        self.manual_unique_button = QPushButton("Manual…")
        self.remove_ignore_button = QPushButton("Quitar")
        self.remove_unique_button = QPushButton("Quitar")
        self.save_targets_button = QPushButton("Guardar")
        self.save_targets_button.setToolTip(
            "Guardar objetivos únicos y checks para el juego seleccionado."
        )
        self.save_targets_button.setEnabled(False)

        for button in (
            self.add_ignore_button,
            self.add_unique_button,
            self.manual_unique_button,
        ):
            button.setFixedHeight(24)
        for button in (self.remove_ignore_button, self.remove_unique_button):
            button.setFixedSize(55, 18)
        self.save_targets_button.setFixedSize(62, 20)

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        attack_row = QHBoxLayout()
        attack_row.setSpacing(6)
        attack_row.addWidget(self.auto_target)
        attack_row.addWidget(self.auto_attack, 1)
        main_layout.addLayout(attack_row)
        main_layout.addWidget(self.auto_loot)
        main_layout.addWidget(self.auto_pot1)
        main_layout.addWidget(self.auto_mp)
        main_layout.addWidget(self.auto_heal)

        options_layout = QHBoxLayout()
        options_layout.setSpacing(5)
        options_layout.addWidget(self.ignore_targets)
        options_layout.addWidget(self.unique_targets_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.save_targets_button)
        main_layout.addLayout(options_layout)

        available_layout = QHBoxLayout()
        available_layout.setSpacing(4)
        available_layout.addWidget(self.available_label)
        available_layout.addWidget(self.available_combo, 1)
        available_layout.addWidget(self.add_ignore_button)
        available_layout.addWidget(self.add_unique_button)
        available_layout.addWidget(self.manual_unique_button)
        main_layout.addLayout(available_layout)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(5)
        lists_layout.addLayout(
            self._create_list_column(
                self.ignored_label,
                self.ignored_list,
                self.remove_ignore_button,
            ),
            1,
        )
        lists_layout.addLayout(
            self._create_list_column(
                self.unique_targets_label,
                self.unique_targets_list,
                self.remove_unique_button,
            ),
            1,
        )
        main_layout.addLayout(lists_layout)

    @staticmethod
    def _create_list_column(label, list_widget, remove_button):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        header = QHBoxLayout()
        header.setSpacing(3)
        header.addWidget(label)
        header.addStretch()
        header.addWidget(remove_button)
        layout.addLayout(header)
        layout.addWidget(list_widget)
        return layout

    def apply_style(self):
        button_style = """
        QPushButton {
            background-color: #173B6D;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 2px 5px;
        }
        QPushButton:hover { background-color: #28558F; }
        QPushButton:pressed { background-color: #102A4D; }
        QPushButton:disabled { background-color: #9CA9B8; }
        """
        for button in self._target_buttons():
            button.setStyleSheet(button_style)
        self.ignore_targets.setStyleSheet("font-size: 10px;")
        self.unique_targets_checkbox.setStyleSheet("font-size: 10px;")

    def connect_signals(self):
        self.add_ignore_button.clicked.connect(self.move_to_ignored)
        self.remove_ignore_button.clicked.connect(self.move_to_available)
        self.add_unique_button.clicked.connect(self.add_unique_target)
        self.manual_unique_button.clicked.connect(self.add_manual_unique_targets)
        self.remove_unique_button.clicked.connect(self.remove_unique_target)
        self.save_targets_button.clicked.connect(
            self.target_filters_save_requested.emit
        )
        self.ignore_targets.stateChanged.connect(self._mark_target_filters_dirty)
        self.unique_targets_checkbox.stateChanged.connect(
            self._mark_target_filters_dirty
        )

    def move_to_ignored(self):
        name = self._current_available_name()
        if not name or self._find_item(self.ignored_list, name):
            return

        self.ignored_list.addItem(name)
        unique_changed = self._remove_unique_target_by_name(name)
        self._sort_list(self.ignored_list)
        self._refresh_available_combo()
        if unique_changed:
            self._unique_targets_updated()
        self._mark_target_filters_dirty()
        self.enemy_ignores_changed.emit([name], True)
        self.enemy_ignore_changed.emit(name, True)

    def move_to_available(self):
        names = self._selected_names(self.ignored_list)
        if not names:
            return
        for name in names:
            self._remove_item_by_name(self.ignored_list, name)
        self._refresh_available_combo()
        self._mark_target_filters_dirty()
        self.enemy_ignores_changed.emit(names, False)
        for name in names:
            self.enemy_ignore_changed.emit(name, False)

    def add_unique_target(self):
        name = self._current_available_name()
        if name:
            self._add_unique_names([name])

    def add_manual_unique_targets(self):
        text, accepted = QInputDialog.getMultiLineText(
            self,
            "Agregar objetivos únicos",
            "Un objetivo por línea:",
            "",
        )
        if accepted:
            self._add_unique_names(text.splitlines())

    def _add_unique_names(self, names):
        added_names = []
        unignored_names = []
        for raw_name in names:
            name = self._canonical_display_name(raw_name)
            if not name or self._contains_unique_target(name):
                continue

            if self._remove_item_by_name(self.ignored_list, name):
                unignored_names.append(name)
            self.unique_targets_list.addItem(name)
            added_names.append(name)

        if not added_names:
            return

        self._sort_list(self.unique_targets_list)
        self._refresh_available_combo()
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
        self._refresh_available_combo()
        self._unique_targets_updated()

    def set_enemy_names(self, enemy_names, ignored_names):
        canonical_names = {
            str(name).strip().casefold(): str(name).strip()
            for name in (*enemy_names, *ignored_names)
            if str(name).strip()
        }
        self._database_enemy_names = sorted(
            canonical_names.values(),
            key=str.casefold,
        )
        ignored_keys = {
            str(name).strip().casefold()
            for name in ignored_names
            if str(name).strip()
        }
        ignored_display_names = sorted(
            (
                canonical_names[key]
                for key in ignored_keys
                if key in canonical_names
            ),
            key=str.casefold,
        )
        self._set_list_items(self.ignored_list, ignored_display_names)

        unique_changed = False
        for name in ignored_display_names:
            unique_changed |= self._remove_unique_target_by_name(name)
        self._refresh_available_combo()
        if unique_changed:
            self._unique_targets_updated()

    def set_target_filters(
        self,
        unique_targets,
        ignore_enabled=False,
        unique_enabled=False,
    ):
        ignored_keys = {
            name.casefold()
            for name in self.get_ignored_targets()
        }
        unique_by_key = {}
        for raw_name in unique_targets:
            name = self._canonical_display_name(raw_name)
            key = name.casefold()
            if name and key not in ignored_keys:
                unique_by_key.setdefault(key, name)

        self._set_list_items(
            self.unique_targets_list,
            sorted(unique_by_key.values(), key=str.casefold),
        )
        ignore_blocker = QSignalBlocker(self.ignore_targets)
        unique_blocker = QSignalBlocker(self.unique_targets_checkbox)
        self.ignore_targets.setChecked(bool(ignore_enabled))
        self.unique_targets_checkbox.setChecked(
            bool(unique_enabled and unique_by_key)
        )
        del ignore_blocker, unique_blocker
        self.unique_targets_checkbox.setEnabled(
            bool(unique_by_key) and not self._controls_locked
        )
        self._refresh_available_combo()
        self.mark_target_filters_saved()

    def get_ignored_targets(self):
        return self._list_names(self.ignored_list)

    def get_unique_targets(self):
        return self._list_names(self.unique_targets_list)

    def get_target_filter_state(self):
        return {
            "ignored_targets": self.get_ignored_targets(),
            "unique_targets": self.get_unique_targets(),
            "ignore_enabled": self.ignore_targets.isChecked(),
            "unique_enabled": self.unique_targets_checkbox.isChecked(),
        }

    def has_unsaved_target_filters(self):
        return self._target_filters_dirty

    def mark_target_filters_saved(self):
        self._target_filters_dirty = False
        self.save_targets_button.setEnabled(False)

    def _mark_target_filters_dirty(self, _value=None):
        self._target_filters_dirty = True
        self.save_targets_button.setEnabled(not self._controls_locked)

    def _unique_targets_updated(self):
        names = self.get_unique_targets()
        if not names:
            checkbox_blocker = QSignalBlocker(self.unique_targets_checkbox)
            self.unique_targets_checkbox.setChecked(False)
            del checkbox_blocker
        self.unique_targets_checkbox.setEnabled(
            bool(names) and not self._controls_locked
        )
        self.unique_targets_changed.emit(names)
        self._mark_target_filters_dirty()

    def _refresh_available_combo(self):
        current = self._current_available_name()
        excluded = {
            name.casefold()
            for name in (
                *self.get_ignored_targets(),
                *self.get_unique_targets(),
            )
        }
        available_names = [
            name
            for name in self._database_enemy_names
            if name.casefold() not in excluded
        ]

        blocker = QSignalBlocker(self.available_combo)
        self.available_combo.clear()
        self.available_combo.addItems(available_names)
        if current:
            index = self.available_combo.findText(current)
            if index >= 0:
                self.available_combo.setCurrentIndex(index)
        del blocker
        enabled = bool(available_names) and not self._controls_locked
        self.available_combo.setEnabled(enabled)
        self.add_ignore_button.setEnabled(enabled)
        self.add_unique_button.setEnabled(enabled)

    def _current_available_name(self):
        return self.available_combo.currentText().strip()

    def _canonical_display_name(self, name):
        name = str(name or "").strip()
        if not name:
            return ""
        normalized = name.casefold()
        for candidate in (
            *self._database_enemy_names,
            *self.get_ignored_targets(),
            *self.get_unique_targets(),
        ):
            if candidate.casefold() == normalized:
                return candidate
        return name

    def _contains_unique_target(self, name):
        return self._find_item(self.unique_targets_list, name) is not None

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

    def _remove_unique_target_by_name(self, name):
        return self._remove_item_by_name(self.unique_targets_list, name)

    @classmethod
    def _sort_list(cls, list_widget):
        cls._set_list_items(
            list_widget,
            sorted(cls._list_names(list_widget), key=str.casefold),
        )

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
        self.save_targets_button.setEnabled(self._target_filters_dirty)
        self._refresh_available_combo()

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
            self.available_combo,
            self.ignored_list,
            self.unique_targets_list,
            *self._target_buttons(),
        )

    def _target_buttons(self):
        return (
            self.add_ignore_button,
            self.remove_ignore_button,
            self.add_unique_button,
            self.manual_unique_button,
            self.remove_unique_button,
            self.save_targets_button,
        )
