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
            SkillCard(f"F{number}") for number in range(1, 8)
        ]
        self.skills = self.number_skills + self.function_skills

        self.priority_header = QLabel("PRIORIDAD")
        self.priority_header.setToolTip(
            "Las habilidades F1–F7 se ejecutan antes que las del 1 al 9 "
            "cuando coinciden, sin adelantar los milisegundos configurados."
        )
        self.priority_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.priority_header.setStyleSheet(
            "font-size: 8px; font-weight: bold; color: #173B6D;"
        )

    def create_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(0)
        grid.addWidget(self.priority_header, 0, 1)

        for row, skill in enumerate(self.number_skills, start=1):
            grid.addWidget(skill, row, 0)
        for row, skill in enumerate(self.function_skills, start=1):
            grid.addWidget(skill, row, 1)

        layout.addLayout(grid)

    def lock_controls(self):
        for skill in self.skills:
            skill.lock()

    def unlock_controls(self):
        for skill in self.skills:
            skill.unlock()
