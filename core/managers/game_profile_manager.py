import json
import os





class GameProfileManager:


    def __init__(

        self,

        path="data/games.json"

    ):


        self.path = path

        self.games = {}

        self.active_game = None


        self.load()







    # =====================================
    # LOAD
    # =====================================


    def load(self):


        if not os.path.exists(

            self.path

        ):

            self.games = {}

            return





        with open(

            self.path,

            "r",

            encoding="utf-8"

        ) as file:


            data = json.load(file)





        self.games = {}



        for game in data.get(

            "games",

            []

        ):


            self.games[

                game["id"]

            ] = game







    # =====================================
    # SAVE
    # =====================================


    def save(self):


        data = {


            "games": list(

                self.games.values()

            )

        }





        with open(

            self.path,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                data,

                file,

                indent=4,

                ensure_ascii=False

            )









    # =====================================
    # LISTAR
    # =====================================


    def get_games(self):

        return list(

            self.games.values()

        )









    # =====================================
    # OBTENER
    # =====================================


    def get_game(

        self,

        game_id

    ):


        return self.games.get(

            game_id

        )









    # =====================================
    # ACTIVO
    # =====================================


    def set_active_game(

        self,

        game_id

    ):


        if game_id not in self.games:

            return False



        self.active_game = self.games[game_id]


        return True







    def get_active_game(self):

        return self.active_game










    # =====================================
    # DATOS PERFIL
    # =====================================


    def get_process(self):

        if not self.active_game:

            return None


        return self.active_game.get(

            "process"

        )







    def get_window(self):

        if not self.active_game:

            return None


        return self.active_game.get(

            "window"

        )








    def get_resolution(self):


        if not self.active_game:


            return (

                1920,

                1080

            )



        resolution = self.active_game.get(

            "resolution",

            {}

        )


        return (

            resolution.get(

                "width",

                1920

            ),


            resolution.get(

                "height",

                1080

            )

        )









    # =====================================
    # AÑADIR JUEGO
    # =====================================


    def add_game(

        self,

        game_id,

        name,

        process,

        window,

        width=1920,

        height=1080

    ):


        self.games[game_id] = {


            "id": game_id,


            "name": name,


            "process": process,


            "window": window,


            "resolution": {


                "width": width,


                "height": height

            }

        }



        self.save()







    # =====================================
    # ELIMINAR
    # =====================================


    def remove_game(

        self,

        game_id

    ):


        if game_id in self.games:


            del self.games[game_id]


            self.save()


            return True



        return False