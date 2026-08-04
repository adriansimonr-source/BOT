class EntityDatabase:


    def __init__(self):


        self.players = {}

        self.enemies = {}

        self.items = {}







    # =====================================
    # PLAYERS
    # =====================================


    def add_player(

        self,

        name,

        data=None

    ):


        if not name:

            return



        if data is None:

            data = {

                "level": 0,

                "class": "",

                "last_seen": None

            }



        self.players[name] = data







    def update_player(

        self,

        name,

        data

    ):


        if name not in self.players:

            self.add_player(

                name,

                data

            )

            return



        self.players[name].update(

            data

        )







    def get_player(

        self,

        name

    ):


        return self.players.get(

            name

        )







    def get_players(self):


        return self.players







    def is_player(

        self,

        name

    ):


        return name in self.players







    def remove_player(

        self,

        name

    ):


        if name in self.players:

            del self.players[name]









    # =====================================
    # ENEMIES
    # =====================================


    def add_enemy(

        self,

        name,

        data=None

    ):


        if not name:

            return


        if name in self.enemies:

            return



        if data is None:


            data = {

                "level": 0,

                "priority": 0,

                "ignore": False,

                "elite": False,

                "boss": False,

                "encounters": 0

            }



        self.enemies[name] = data







    def update_enemy(

        self,

        name,

        data

    ):


        if name not in self.enemies:


            self.add_enemy(

                name,

                data

            )

            return



        self.enemies[name].update(

            data

        )







    def register_enemy_encounter(

        self,

        name

    ):


        if name not in self.enemies:

            self.add_enemy(

                name

            )



        self.enemies[name]["encounters"] = (
            self.enemies[name].get("encounters", 0) + 1
        )







    def get_enemy(

        self,

        name

    ):


        return self.enemies.get(

            name

        )







    def get_enemies(self):


        return self.enemies







    def is_enemy(

        self,

        name

    ):


        return name in self.enemies







    def remove_enemy(

        self,

        name

    ):


        if name in self.enemies:

            del self.enemies[name]









    # =====================================
    # FILTROS ENEMIGOS
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







    def is_elite(

        self,

        name

    ):


        enemy = self.get_enemy(

            name

        )



        if enemy is None:

            return False



        return enemy.get(

            "elite",

            False

        )









    # =====================================
    # ITEMS (PREPARADO)
    # =====================================


    def add_item(

        self,

        name,

        data=None

    ):


        if not name or name in self.items:

            return


        if data is None:

            data = {

                "keep": False,

                "value": 0,

                "encounters": 0

            }



        self.items[name] = data





    def register_item_encounter(

        self,

        name

    ):


        if name not in self.items:

            self.add_item(name)


        self.items[name]["encounters"] = (

            self.items[name].get("encounters", 0) + 1

        )







    def get_item(

        self,

        name

    ):


        return self.items.get(

            name

        )







    def get_items(self):


        return self.items





    def is_item(self, name):


        return name in self.items
