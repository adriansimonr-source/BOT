import time





class EntityCacheManager:


    def __init__(self):


        # ==========================
        # PLAYER
        # ==========================


        self.player_name_loaded = False


        self.player_level_time = 0


        self.player_level_refresh = 1800





        # ==========================
        # ENEMY
        # ==========================


        self.current_enemy_name = ""


        self.current_enemy_level = 0


        self.enemy_detected_time = 0







    # =====================================
    # PLAYER NAME
    # =====================================


    def need_player_name(self):

        return not self.player_name_loaded





    def player_name_loaded_ok(self):

        self.player_name_loaded = True


    def reset_player_name(self):

        self.player_name_loaded = False







    # =====================================
    # PLAYER LEVEL
    # =====================================


    def need_player_level(self):


        return (

            time.time()

            -

            self.player_level_time

        ) >= self.player_level_refresh







    def update_player_level_time(self):


        self.player_level_time = time.time()







    # =====================================
    # ENEMY
    # =====================================


    def enemy_changed(

        self,

        name

    ):


        if not name:

            return False



        return (

            name != self.current_enemy_name

        )







    def update_enemy(

        self,

        name,

        level

    ):


        self.current_enemy_name = name


        self.current_enemy_level = level


        self.enemy_detected_time = time.time()







    def clear_enemy(self):


        self.current_enemy_name = ""


        self.current_enemy_level = 0


        self.enemy_detected_time = 0
