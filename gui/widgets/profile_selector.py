from PySide6.QtCore import QSize, QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QWidget,
)


class ProfileSelector(QWidget):
    profile_selected = Signal(str)
    save_requested = Signal(str)
    delete_requested = Signal(str)

    NO_PROFILE_TEXT = "Sin perfil"

    def __init__(self):
        super().__init__()
        self._locked = False

        self.title_label = QLabel("PERFIL")
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setToolTip(
            "Configuración opcional de checks, umbrales y tiempos."
        )

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.setDuplicatesEnabled(False)
        self.combo.setMinimumContentsLength(10)
        self.combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.combo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.combo.lineEdit().setMaxLength(40)
        self.combo.setToolTip(
            "Selecciona un perfil para aplicarlo o escribe un nombre nuevo. "
            "Sin perfil permite configurar la GUI libremente."
        )

        self.save_button = QPushButton()
        self.save_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogSaveButton
            )
        )
        self.save_button.setIconSize(QSize(14, 14))
        self.save_button.setFixedSize(22, 20)
        self.save_button.setAccessibleName("Guardar perfil")
        self.save_button.setToolTip(
            "Crea el perfil escrito o actualiza el perfil seleccionado con "
            "la configuración actual."
        )

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(22, 20)
        self.delete_button.setAccessibleName("Eliminar perfil")
        self.delete_button.setToolTip(
            "Elimina el perfil seleccionado después de confirmarlo."
        )

        button_style = """
            QPushButton {
                background-color: #173B6D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton:hover { background-color: #28558F; }
            QPushButton:pressed { background-color: #102A4D; }
            QPushButton:disabled { background-color: #9CA9B8; }
        """
        self.save_button.setStyleSheet(button_style)
        self.delete_button.setStyleSheet(button_style)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(self.title_label)
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.save_button)
        layout.addWidget(self.delete_button)

        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Fixed,
        )
        self.set_profiles(())
        self.combo.currentIndexChanged.connect(self._emit_selection)
        self.combo.editTextChanged.connect(self._update_delete_state)
        self.save_button.clicked.connect(self._emit_save)
        self.delete_button.clicked.connect(self._emit_delete)

    def set_profiles(self, names, selected_name=None):
        unique_names = {}
        for name in names:
            display_name = str(name or "").strip()
            if display_name:
                unique_names.setdefault(display_name.casefold(), display_name)

        profiles = sorted(unique_names.values(), key=str.casefold)
        selected_key = str(selected_name or "").strip().casefold()

        blocker = QSignalBlocker(self.combo)
        self.combo.clear()
        self.combo.addItem(self.NO_PROFILE_TEXT, "")
        for name in profiles:
            self.combo.addItem(name, name)

        selected_index = 0
        if selected_key:
            for index in range(1, self.combo.count()):
                if str(self.combo.itemData(index)).casefold() == selected_key:
                    selected_index = index
                    break
        self.combo.setCurrentIndex(selected_index)
        del blocker
        self._update_delete_state()

    def selected_name(self):
        stored_name = str(self.combo.currentData() or "").strip()
        typed_name = self.combo.currentText().strip()
        if stored_name and typed_name.casefold() == stored_name.casefold():
            return stored_name

        if typed_name.casefold() == self.NO_PROFILE_TEXT.casefold():
            return ""
        return typed_name

    def selected_stored_name(self):
        stored_name = str(self.combo.currentData() or "").strip()
        typed_name = self.combo.currentText().strip()
        if stored_name and typed_name.casefold() == stored_name.casefold():
            return stored_name
        return ""

    def set_locked(self, locked):
        self._locked = bool(locked)
        self.combo.setEnabled(not self._locked)
        self.save_button.setEnabled(not self._locked)
        self._update_delete_state()

    def _emit_selection(self, _index):
        self._update_delete_state()
        self.profile_selected.emit(str(self.combo.currentData() or ""))

    def _emit_save(self):
        self.save_requested.emit(self.selected_name())

    def _emit_delete(self):
        self.delete_requested.emit(self.selected_stored_name())

    def _update_delete_state(self, *_args):
        self.delete_button.setEnabled(
            not self._locked and bool(self.selected_stored_name())
        )
