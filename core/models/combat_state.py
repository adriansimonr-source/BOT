class CombatState:


    def __init__(self):

        self.player_detected = False

        self.player_hp = 0

        self.player_mp = 0


        self.enemy_detected = False

        self.enemy_hp = 0



    def reset(self):

        self.player_detected = False

        self.player_hp = 0

        self.player_mp = 0


        self.enemy_detected = False

        self.enemy_hp = 0




    def to_dict(self):

        return {

            "player_detected":
                self.player_detected,

            "player_hp":
                self.player_hp,

            "player_mp":
                self.player_mp,


            "enemy_detected":
                self.enemy_detected,

            "enemy_hp":
                self.enemy_hp

        }