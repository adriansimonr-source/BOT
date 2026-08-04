from core.models.player_state import PlayerState


class PlayerMonitor:

    def __init__(
        self,
        detector,
        resolver,
        bar_reader,
        templates,
        name_matcher,
        entity_cache,
        entity_database,
        executor=None,
    ):
        self.detector = detector
        self.resolver = resolver
        self.bar_reader = bar_reader
        self.templates = templates
        self.name_matcher = name_matcher
        self.entity_cache = entity_cache
        self.entity_database = entity_database
        self.executor = executor
        self.identity_future = None
        self.identity_generation = 0

    def set_executor(self, executor):
        self.executor = executor

    def update(self, image, player_state: PlayerState):
        self.poll(player_state)
        if image is None:
            return False

        anchor_template = self.templates.get("player_anchor")
        if anchor_template is None:
            return False
        player_anchor = self.detector.detect(image, anchor_template)
        if not player_anchor:
            return False

        hud_template = self.templates.get("player_hud")
        if hud_template is None:
            return False
        player_hud = self.resolver.resolve(player_anchor, hud_template)
        if not player_hud:
            return False

        hud_image = self.resolver.crop(image, player_hud)
        if hud_image is None:
            return False

        self.read_resources(hud_image, player_state)
        if self.executor is None:
            self.read_identity(hud_image, player_state)
        else:
            self._schedule_identity(hud_image)
        return True

    def poll(self, player_state):
        future = self.identity_future
        if future is None or not future.done():
            return

        self.identity_future = None
        try:
            generation, name, level, attempted_level = future.result()
        except Exception:
            return
        if generation != self.identity_generation:
            return

        if name:
            player_state.name = name
            self.entity_cache.player_name_loaded_ok()
        if level > 0:
            player_state.level = level
        if attempted_level:
            self.entity_cache.update_player_level_time()

    def refresh_name(self, player_state=None):
        self.identity_generation += 1
        self.entity_cache.reset_player_name()
        if player_state is not None:
            player_state.name = ""
        if self.identity_future and self.identity_future.cancel():
            self.identity_future = None

    def _schedule_identity(self, hud_image):
        if self.identity_future is not None:
            return

        need_name = self.entity_cache.need_player_name()
        need_level = self.entity_cache.need_player_level()
        if not need_name and not need_level:
            return

        name_image = None
        level_image = None
        if need_name:
            name_image = self.crop_region(
                hud_image,
                self.templates.get("player_name"),
            )
        if need_level:
            level_image = self.crop_region(
                hud_image,
                self.templates.get("player_level"),
            )

        generation = self.identity_generation
        self.identity_future = self.executor.submit(
            self._read_identity_data,
            generation,
            name_image.copy() if name_image is not None else None,
            level_image.copy() if level_image is not None else None,
        )

    def _read_identity_data(self, generation, name_image, level_image):
        name = None
        level = 0
        if name_image is not None:
            detected_name = self.name_matcher.read_player_name(name_image)
            if self.valid_name(detected_name):
                name = self.entity_database.resolve_player_name(detected_name)
        if level_image is not None:
            level = self.name_matcher.read_number(level_image)
        return generation, name, level, level_image is not None

    def read_identity(self, hud_image, player_state):
        need_name = self.entity_cache.need_player_name()
        need_level = self.entity_cache.need_player_level()
        name_image = self.crop_region(
            hud_image,
            self.templates.get("player_name"),
        ) if need_name else None
        level_image = self.crop_region(
            hud_image,
            self.templates.get("player_level"),
        ) if need_level else None
        _, name, level, attempted_level = self._read_identity_data(
            self.identity_generation,
            name_image,
            level_image,
        )
        if name:
            player_state.name = name
            self.entity_cache.player_name_loaded_ok()
        if level > 0:
            player_state.level = level
        if attempted_level:
            self.entity_cache.update_player_level_time()

    def read_resources(self, hud_image, player_state):
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("player_hp"),
        )
        if hp_image is not None:
            player_state.hp_percent = self.bar_reader.read_hp(hp_image)

        mp_image = self.crop_region(
            hud_image,
            self.templates.get("player_mp"),
        )
        if mp_image is not None:
            player_state.mp_percent = self.bar_reader.read_mp(mp_image)

    @staticmethod
    def valid_name(name):
        return bool(name and len(name) >= 2)

    @staticmethod
    def crop_region(image, region):
        if image is None or region is None:
            return None
        x = region.get("x", 0)
        y = region.get("y", 0)
        width = region.get("width", 0)
        height = region.get("height", 0)
        if width <= 0 or height <= 0:
            return None
        return image[y:y + height, x:x + width]
