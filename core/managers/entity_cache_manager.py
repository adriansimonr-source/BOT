class EntityCacheManager:

    def __init__(self):

        self.player_name_loaded = False

        self.last_player_level_scan = 0

        self.current_enemy = ""


    def need_player_name(self):

        return not self.player_name_loaded


    def need_player_level(self):

        return (
            time.time() -
            self.last_player_level_scan
            > 1800
        )


    def enemy_changed(self,name):

        return name != self.current_enemy