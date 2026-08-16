from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from gui.widgets.skill_card import SkillCard


class CenterPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.number_skills = [SkillCard(number) for number in range(1, 10)]
        self.function_skills = [
            SkillCard(f"F{number}") for number in range(1, 10)
        ]
        self.skills = self.number_skills + self.function_skills

        self.number_header = QLabel("1–9\nHABILIDADES")
        self.priority_header = QLabel("F1–F9 · PRIORIDAD\nBUFFS / ESCUDOS")
        self.priority_header.setToolTip(
            "Cuando coinciden acciones pendientes, F1–F9 obtiene el primer "
            "turno sin adelantar los milisegundos configurados."
        )
        for header in (self.number_header, self.priority_header):
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setStyleSheet(
                "font-size: 9px; font-weight: bold; color: #173B6D;"
            )

    def create_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)
        grid.addWidget(self.number_header, 0, 0)
        grid.addWidget(self.priority_header, 0, 1)

        for row in range(9):
            grid.addWidget(self.number_skills[row], row + 1, 0)
            grid.addWidget(self.function_skills[row], row + 1, 1)

        layout.addLayout(grid)

    def lock_controls(self):
        for skill in self.skills:
            skill.lock()

    def unlock_controls(self):
        for skill in self.skills:
            skill.unlock()
