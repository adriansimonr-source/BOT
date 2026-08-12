import time


class EntityCacheManager:
    def __init__(self):
        self.current_enemy_name = ""
        self.current_enemy_level = 0
        self.enemy_detected_time = 0

    def enemy_changed(self, name):
        if not name:
            return False
        return name != self.current_enemy_name

    def update_enemy(self, name, level):
        self.current_enemy_name = name
        self.current_enemy_level = level
        self.enemy_detected_time = time.time()

    def clear_enemy(self):
        self.current_enemy_name = ""
        self.current_enemy_level = 0
        self.enemy_detected_time = 0
