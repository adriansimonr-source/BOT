import json
import os

from difflib import SequenceMatcher

from core.databases.entity_database import EntityDatabase





class EntityDatabaseManager:


    def __init__(

        self,

        path="data/entities"

    ):


        self.path = path


        self.database = EntityDatabase()



        self.players_file = os.path.join(

            path,

            "players.json"

        )


        self.enemies_file = os.path.join(

            path,

            "enemies.json"

        )


        self.items_file = os.path.join(

            path,

            "items.json"

        )



        self.load()







    # =====================================
    # LOAD / SAVE
    # =====================================


    def load(self):


        self.load_file(

            self.players_file,

            self.database.players

        )


        self.load_file(

            self.enemies_file,

            self.database.enemies

        )


        self.load_file(

            self.items_file,

            self.database.items

        )








    def load_file(

        self,

        file,

        container

    ):


        if not os.path.exists(file):

            return



        with open(

            file,

            "r",

            encoding="utf-8"

        ) as f:


            data = json.load(f)



        container.update(

            data

        )









    def save(self):


        os.makedirs(

            self.path,

            exist_ok=True

        )


        self.save_file(

            self.players_file,

            self.database.players

        )


        self.save_file(

            self.enemies_file,

            self.database.enemies

        )


        self.save_file(

            self.items_file,

            self.database.items

        )







    def save_file(

        self,

        file,

        data

    ):


        with open(

            file,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                data,

                f,

                indent=4,

                ensure_ascii=False

            )









    # =====================================
    # NAME RESOLUTION
    # =====================================


    def resolve_enemy_name(

        self,

        name

    ):


        if not name:

            return None



        if self.database.is_enemy(

            name

        ):

            return name





        similar = self.find_similar(

            name,

            self.database.get_enemies()

        )



        if similar:

            return similar





        self.database.add_enemy(

            name

        )


        self.save()



        return name







    def resolve_player_name(

        self,

        name

    ):


        if not name:

            return None



        if self.database.is_player(

            name

        ):

            return name





        similar = self.find_similar(

            name,

            self.database.get_players()

        )



        if similar:

            return similar





        self.database.add_player(

            name

        )


        self.save()



        return name







    # =====================================
    # SIMILITUD OCR
    # =====================================


    def find_similar(

        self,

        name,

        collection,

        threshold=0.85

    ):


        best_name = None

        best_score = 0



        for current in collection.keys():


            score = SequenceMatcher(

                None,

                name.lower(),

                current.lower()

            ).ratio()



            if score > best_score:


                best_score = score

                best_name = current





        if best_score >= threshold:


            return best_name





        return None







    # =====================================
    # ENEMIES
    # =====================================


    def get_enemy(

        self,

        name

    ):


        return self.database.get_enemy(

            name

        )







    def should_ignore_enemy(

        self,

        name

    ):


        return self.database.should_ignore_enemy(

            name

        )







    def get_enemy_priority(

        self,

        name

    ):


        return self.database.get_priority(

            name

        )







    def register_enemy_seen(

        self,

        name

    ):


        self.database.register_enemy_encounter(

            name

        )


        self.save()







    # =====================================
    # PLAYERS
    # =====================================


    def get_player(

        self,

        name

    ):


        return self.database.get_player(

            name

        )







    # =====================================
    # ITEMS
    # =====================================


    def add_item(

        self,

        name,

        data=None

    ):


        self.database.add_item(

            name,

            data

        )


        self.save()