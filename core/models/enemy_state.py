class EnemyState:


    def __init__(self):


        self.exists = False



        self.name = ""

        self.level = 0



        self.hp_percent = 0



        self.distance = 0


        self.visible = False



        self.is_elite = False

        self.is_boss = False




        self.targetable = False

        self.priority = 0




    def clear(self):


        self.exists = False


        self.name = ""

        self.level = 0


        self.hp_percent = 0



        self.distance = 0


        self.visible = False


        self.is_elite = False

        self.is_boss = False


        self.targetable = False

        self.priority = 0