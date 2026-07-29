from PySide6.QtWidgets import QComboBox, QGroupBox, QLabel, QVBoxLayout

class ProfileGroup(QGroupBox):

    def __init__(self):
        super().__init__("PERFIL")
        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.addWidget(QLabel("PERFIL ACTUAL"))
        self.profile_selector = QComboBox()
        self.profile_selector.addItem("Default")
        layout.addWidget(self.profile_selector)

        self.setLayout(layout)

    def add_profile(self, profile_name: str):
        self.profile_selector.addItem(self.profile_name)

    def clear_profiles(self):
        self.profile_selector.clear()

    def current_profile(self) -> str:
        return self.profile_selector.currentText()

    def set_current_profile(self, profile_name: str):
        index = self.profile_selector.findText(profile_name)
        if index >= 0:
            self.profile_selector.setCurrentIndex(index)

