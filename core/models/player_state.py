class PlayerState:

    def __init__(self):

        self.name = ""

        self.level = 0

        self.hp = 0
        self.max_hp = 0

        self.mp = 0
        self.max_mp = 0

        self.x = 0
        self.y = 0
        self.z = 0


    def hp_percentage(self):

        if self.max_hp <= 0:
            return 0

        return int(
            (self.hp / self.max_hp) * 100
        )