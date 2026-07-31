class TargetState:


    def __init__(self):


        # ==========================
        # Existencia
        # ==========================

        self.exists = False



        # ==========================
        # Información básica
        # ==========================

        self.name = ""

        self.level = 0





        # ==========================
        # Vida
        # ==========================

        self.hp_percent = 0.0





        # ==========================
        # Estado visual
        # ==========================

        self.visible = False


        self.targetable = False







    # ==========================
    # Reset
    # ==========================

    def reset(self):


        self.exists = False


        self.name = ""

        self.level = 0


        self.hp_percent = 0.0


        self.visible = False


        self.targetable = False