class EntityDatabase:


    def __init__(self):


        self.players = {}

        self.enemies = {}




    # =====================================
    # PLAYERS
    # =====================================


    def add_player(

        self,

        name,

        data=None

    ):


        if data is None:

            data = {}


        self.players[name] = data





    def get_player(

        self,

        name

    ):


        return self.players.get(

            name

        )





    def is_player(

        self,

        name

    ):


        return name in self.players







    # =====================================
    # ENEMIES
    # =====================================


    def add_enemy(

        self,

        name,

        data=None

    ):


        if data is None:

            data = {

                "priority": 0,

                "ignore": False,

                "elite": False,

                "boss": False

            }


        self.enemies[name] = data





    def get_enemy(

        self,

        name

    ):


        return self.enemies.get(

            name

        )





    def is_enemy(

        self,

        name

    ):


        return name in self.enemies







    # =====================================
    # FILTROS
    # =====================================


    def should_ignore_enemy(

        self,

        name

    ):


        enemy = self.get_enemy(

            name

        )


        if enemy is None:

            return False



        return enemy.get(

            "ignore",

            False

        )







    def get_priority(

        self,

        name

    ):


        enemy = self.get_enemy(

            name

        )


        if enemy is None:

            return 0



        return enemy.get(

            "priority",

            0

        )







    def is_boss(

        self,

        name

    ):


        enemy = self.get_enemy(

            name

        )


        if enemy is None:

            return False



        return enemy.get(

            "boss",

            False

        )