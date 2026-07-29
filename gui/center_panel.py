from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
)

from gui.widgets.skill_card import SkillCard


class CenterPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):

        self.skills_group = QGroupBox("SKILLS")

        self.skills = []

        for i in range(1, 10):
            self.skills.append(SkillCard(i))

    def create_layout(self):

        skills_layout = QVBoxLayout()

        for skill in self.skills:
            skills_layout.addWidget(skill)

        skills_layout.addStretch()

        self.skills_group.setLayout(skills_layout)

        layout = QVBoxLayout(self)

        layout.addWidget(self.skills_group)
        layout.addStretch()

        self.setLayout(layout)