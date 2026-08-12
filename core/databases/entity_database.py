class EntityDatabase:
    def __init__(self):
        self.enemies = {}
        self.items = {}

    def add_enemy(self, name, data=None):
        if not name or name in self.enemies:
            return
        if data is None:
            data = {
                "level": 0,
                "priority": 0,
                "ignore": False,
                "elite": False,
                "boss": False,
                "encounters": 0,
            }
        self.enemies[name] = data

    def update_enemy(self, name, data):
        if name not in self.enemies:
            self.add_enemy(name, data)
            return
        self.enemies[name].update(data)

    def register_enemy_encounter(self, name):
        if name not in self.enemies:
            self.add_enemy(name)
        self.enemies[name]["encounters"] = (
            self.enemies[name].get("encounters", 0) + 1
        )

    def get_enemy(self, name):
        return self.enemies.get(name)

    def get_enemies(self):
        return self.enemies

    def is_enemy(self, name):
        return name in self.enemies

    def should_ignore_enemy(self, name):
        enemy = self.get_enemy(name)
        return bool(enemy and enemy.get("ignore", False))

    def add_item(self, name, data=None):
        if not name or name in self.items:
            return
        if data is None:
            data = {"keep": False, "value": 0, "encounters": 0}
        self.items[name] = data

    def register_item_encounter(self, name):
        if name not in self.items:
            self.add_item(name)
        self.items[name]["encounters"] = (
            self.items[name].get("encounters", 0) + 1
        )

    def get_item(self, name):
        return self.items.get(name)

    def get_items(self):
        return self.items
