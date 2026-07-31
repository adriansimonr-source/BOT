class PlayerState:


    def __init__(self):

        # ==============================
        self.name = ""
        self.level = 0
        self.hp_percent = 0
        self.mp_percent = 0
        self.x = 0
        self.y = 0
        self.z = 0


    def reset(self):

        self.name = ""
        self.level = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.hp_percent = 0
        self.mp_percent = 0


    def to_dict(self):

        return {

            "name": self.name,

            "level": self.level,

            "hp_percent": self.hp_percent,

            "mp_percent": self.mp_percent,

            "x": self.x,

            "y": self.y,

            "z": self.z

        }