from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox, 
    QGridLayout,
)

from gui.widgets.skill_card import SkillCard

class CenterPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):

        self.skills_group = QGroupBox("ROTACION")

        self.skills = []

        for i in range(1, 10):
            self.skills.append(SkillCard(i))

    def create_layout(self):

        skills_layout = QGridLayout()
        skills_layout.setHorizontalSpacing(10)
        skills_layout.setVerticalSpacing(5)

        for i, skill in enumerate(self.skills):

            if i < 5:
                row = 0
                column = i
            else:
                row = 1
                column = i - 5

            skills_layout.addWidget(skill, row, column)

        self.skills_group.setLayout(skills_layout)

        layout = QVBoxLayout(self)

        layout.addWidget(self.skills_group)
        layout.addStretch()

        self.setLayout(layout)