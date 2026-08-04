import cv2
import numpy as np

from core.models.target_state import TargetState
from core.services.target_validator import TargetValidator


class EnemyMonitor:

    ENTITY_ENEMY = "enemy"
    ENTITY_ITEM = "item"
    SIGNATURE_DIFFERENCE = 0.18

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
        target_validator=None,
    ):
        self.detector = detector
        self.resolver = resolver
        self.bar_reader = bar_reader
        self.templates = templates
        self.name_matcher = name_matcher
        self.entity_cache = entity_cache
        self.entity_database = entity_database
        self.executor = executor
        self.target_validator = target_validator or TargetValidator()
        self.identity_future = None
        self.selection_id = 0
        self.target_visible = False
        self.current_signature = None
        self.current_entity_type = None
        self.recognized_signature = None
        self.recognized_name = ""
        self.recognized_level = 0
        self.recognized_entity_type = None

    def set_executor(self, executor):
        self.executor = executor

    def update(self, image, target_state: TargetState):
        self.poll(target_state)
        if image is None:
            return False

        target_state.reset(clear_selection=False)
        anchor_template = self.templates.get("enemy_anchor")
        if anchor_template is None:
            self._target_missing()
            return False
        enemy_anchor = self.detector.detect(image, anchor_template)
        if not enemy_anchor:
            self._target_missing()
            return False

        hud_template = self.templates.get("enemy_hud")
        if hud_template is None:
            self._target_missing()
            return False
        enemy_hud = self.resolver.resolve(enemy_anchor, hud_template)
        if not enemy_hud:
            self._target_missing()
            return False
        hud_image = self.resolver.crop(image, enemy_hud)
        if hud_image is None:
            self._target_missing()
            return False

        name_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_name"),
        )
        signature = self._create_signature(name_image)
        has_hp_bar, hp_percent = self._read_health_data(hud_image)
        entity_type = (
            self.ENTITY_ENEMY if has_hp_bar else self.ENTITY_ITEM
        )

        if (
            not self.target_visible
            or self._signature_changed(signature)
            or entity_type != self.current_entity_type
        ):
            self._new_selection(signature, entity_type)
        else:
            self.current_signature = signature

        target_state.selection_id = self.selection_id
        target_state.visible = True
        target_state.exists = has_hp_bar
        target_state.targetable = has_hp_bar
        target_state.hp_percent = hp_percent if has_hp_bar else 0.0
        self._apply_cached_identity(target_state, signature)

        if self.executor is None:
            self.read_identity(
                hud_image,
                target_state,
                signature,
                entity_type,
            )
        else:
            self._schedule_identity(hud_image, signature, entity_type)
            target_state.identity_pending = (
                entity_type == self.ENTITY_ENEMY
                and self.recognized_entity_type is None
            )
        return True

    def poll(self, target_state):
        future = self.identity_future
        if future is None or not future.done():
            return

        self.identity_future = None
        try:
            result = future.result()
            selection_id, signature, name, level, entity_type = (
                self._unpack_identity_result(result)
            )
        except Exception:
            return
        if (
            selection_id != self.selection_id
            or not name
            or entity_type != self.current_entity_type
        ):
            return
        if self._signature_changed_from(signature, self.current_signature):
            return

        self._remember_identity(signature, name, level, entity_type)
        target_state.identity_pending = False
        if target_state.exists and entity_type == self.ENTITY_ENEMY:
            target_state.name = name
            target_state.level = level

    def _target_missing(self):
        if not self.target_visible:
            return
        self.target_visible = False
        self.current_signature = None
        self.current_entity_type = None
        self._clear_recognized_identity()
        self._clear_enemy_cache()

    def _new_selection(self, signature, entity_type):
        self.selection_id += 1
        self.target_visible = True
        self.current_signature = signature
        self.current_entity_type = entity_type
        self._clear_recognized_identity()
        if entity_type != self.ENTITY_ENEMY:
            self._clear_enemy_cache()

    def _clear_recognized_identity(self):
        self.recognized_signature = None
        self.recognized_name = ""
        self.recognized_level = 0
        self.recognized_entity_type = None

    def _clear_enemy_cache(self):
        clear = getattr(self.entity_cache, "clear_enemy", None)
        if callable(clear):
            clear()

    def _remember_identity(self, signature, name, level, entity_type):
        self.recognized_signature = signature
        self.recognized_name = name
        self.recognized_level = level
        self.recognized_entity_type = entity_type

    def _apply_cached_identity(self, target_state, signature):
        if (
            self.recognized_entity_type != self.ENTITY_ENEMY
            or not self.recognized_name
            or self._signature_changed_from(
                signature,
                self.recognized_signature,
            )
        ):
            return
        target_state.name = self.recognized_name
        target_state.level = self.recognized_level
        target_state.identity_pending = False

    def _schedule_identity(self, hud_image, signature, entity_type):
        if self.identity_future is not None or self.recognized_entity_type:
            return
        self.identity_future = self.executor.submit(
            self._read_identity_data,
            self.selection_id,
            signature,
            hud_image.copy(),
            entity_type,
        )

    def _read_identity_data(
        self,
        selection_id,
        signature,
        hud_image,
        entity_type=ENTITY_ENEMY,
    ):
        empty_result = (selection_id, signature, None, 0, None)
        name_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_name"),
        )
        if name_image is None:
            return empty_result
        name = self.name_matcher.read_enemy_name(name_image)
        if not self.valid_name(name):
            return empty_result

        if entity_type == self.ENTITY_ITEM:
            resolver = getattr(self.entity_database, "resolve_item_name", None)
            if not callable(resolver):
                return empty_result
            name = resolver(name)
            if not name:
                return empty_result
            register = getattr(self.entity_database, "register_item_seen", None)
            if callable(register):
                register(name)
            return selection_id, signature, name, 0, self.ENTITY_ITEM

        name = self.entity_database.resolve_enemy_name(name)
        if not name:
            return empty_result
        level = self.entity_cache.current_enemy_level
        if self.entity_cache.enemy_changed(name):
            level_image = self.crop_region(
                hud_image,
                self.templates.get("enemy_level"),
            )
            level = (
                self.name_matcher.read_number(level_image)
                if level_image is not None
                else 0
            )
            self.entity_cache.update_enemy(name, level)
        self.entity_database.register_enemy_seen(name)
        return selection_id, signature, name, level, self.ENTITY_ENEMY

    def read_identity(
        self,
        hud_image,
        target_state,
        signature=None,
        entity_type=ENTITY_ENEMY,
    ):
        result = self._read_identity_data(
            self.selection_id,
            signature,
            hud_image,
            entity_type,
        )
        _, signature, name, level, resolved_type = (
            self._unpack_identity_result(result)
        )
        if not name:
            return False
        self._remember_identity(signature, name, level, resolved_type)
        target_state.identity_pending = False
        if resolved_type == self.ENTITY_ENEMY and target_state.exists:
            target_state.name = name
            target_state.level = level
        return resolved_type == self.ENTITY_ENEMY

    def read_health(self, hud_image, target_state):
        has_hp_bar, hp_percent = self._read_health_data(hud_image)
        target_state.hp_percent = hp_percent if has_hp_bar else 0.0
        return has_hp_bar

    def _read_health_data(self, hud_image):
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_hp"),
        )
        if hp_image is None or not self.target_validator.has_red_bar(hp_image):
            return False, 0.0
        return True, self.bar_reader.read_enemy_hp(hp_image)

    def valid_name(self, name):
        validator = getattr(
            self.entity_database,
            "is_valid_entity_name",
            None,
        )
        if callable(validator):
            return validator(name)
        normalized = str(name or "").strip()
        return bool(
            len(normalized) >= 2
            and sum(character.isalpha() for character in normalized) >= 2
        )

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

    def _signature_changed(self, signature):
        return self._signature_changed_from(signature, self.current_signature)

    @classmethod
    def _signature_changed_from(cls, first, second):
        return bool(
            first is not None
            and second is not None
            and not cls._same_signature(first, second)
        )

    @staticmethod
    def _create_signature(image):
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (32, 8), interpolation=cv2.INTER_AREA)
        return resized >= 150

    @classmethod
    def _same_signature(cls, first, second):
        if first is None or second is None or first.shape != second.shape:
            return False
        return float(np.mean(first != second)) <= cls.SIGNATURE_DIFFERENCE

    @classmethod
    def _unpack_identity_result(cls, result):
        if len(result) == 5:
            return result
        selection_id, signature, name, level = result
        return selection_id, signature, name, level, cls.ENTITY_ENEMY
