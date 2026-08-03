from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
)

from gui.widgets.skill_card import SkillCard





class CenterPanel(QWidget):


    def __init__(self):

        super().__init__()

        self.create_widgets()

        self.create_layout()





    def create_widgets(self):


        self.number_skills = [

            SkillCard(i)

            for i in range(1, 10)

        ]


        self.function_skills = [

            SkillCard(f"F{i}")

            for i in range(1, 10)

        ]


        # Compatibilidad con RotationManager

        self.skills = (

            self.number_skills +

            self.function_skills

        )







    def create_layout(self):


        layout = QVBoxLayout(
            self
        )


        layout.setContentsMargins(
            2,
            2,
            2,
            2
        )


        layout.setSpacing(
            0
        )



        grid = QGridLayout()


        grid.setContentsMargins(
            0,
            0,
            0,
            0
        )


        grid.setHorizontalSpacing(
            12
        )


        grid.setVerticalSpacing(
            2
        )



        for row in range(9):


            grid.addWidget(

                self.number_skills[row],

                row,

                0

            )


            grid.addWidget(

                self.function_skills[row],

                row,

                1

            )



        layout.addLayout(
            grid
        )


        self.setLayout(
            layout
        )








    def lock_controls(self):


        for skill in self.skills:

            skill.lock()






    def unlock_controls(self):


        for skill in self.skills:

            skill.unlock()