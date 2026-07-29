class EnemyState:


    def __init__(self):

        # Existe actualmente

        self.exists = False


        # =========================
        # Información básica
        # =========================

        self.name = ""

        self.level = 0


        # =========================
        # Vida
        # =========================

        self.hp = 0

        self.max_hp = 0


        # =========================
        # Posición
        # =========================

        self.distance = 0


        # =========================
        # Estado visual
        # =========================

        self.visible = False


        # =========================
        # Tipo enemigo
        # =========================

        self.is_elite = False

        self.is_boss = False



    def clear(self):

        self.exists = False

        self.name = ""

        self.level = 0

        self.hp = 0

        self.max_hp = 0

        self.distance = 0

        self.visible = False