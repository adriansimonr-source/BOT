import time

import cv2
import numpy as np

from core.models.target_state import TargetState
from core.services.target_validator import TargetValidator


class EnemyMonitor:

    ENTITY_ENEMY = "enemy"
    ENTITY_ITEM = "item"
    SIGNATURE_DIFFERENCE = 0.18
    HEALTH_MEASURED = "measured"
    HEALTH_EMPTY = "empty"
    HEALTH_INVALID = "invalid"
    HP_ACQUIRE_TIMEOUT_SECONDS = 1.0
    HP_EMPTY_CONFIRMATIONS = 5
    HP_EMPTY_CONFIRMATION_SECONDS = 0.5
    HP_LAST_VALID_SECONDS = 0.75
    TARGET_MISS_CONFIRMATIONS = 3
    ANCHOR_LOCAL_MARGIN = 24
    ANCHOR_INITIAL_RETRY_SECONDS = 0.5
    ANCHOR_RELOCATION_RETRY_SECONDS = 5.0
    IDENTITY_RETRY_SECONDS = 1.0
    MAX_IDENTITY_ATTEMPTS = 3

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
        self.selection_started_at = None
        self.last_valid_hp = None
        self.last_valid_hp_at = None
        self.empty_hp_frames = 0
        self.health_dead = False
        self.empty_hp_started_at = None
        self.missing_hud_frames = 0
        self.anchor_detection = None
        self.last_anchor_confirmation_at = None
        self.force_full_anchor_search = False
        self.identity_attempts = 0
        self.next_identity_retry_at = 0.0

    def set_executor(self, executor):
        self.executor = executor

    def update(self, image, target_state: TargetState):
        self.poll(target_state)
        if image is None:
            return False

        anchor_template = self.templates.get("enemy_anchor")
        if anchor_template is None:
            return self._handle_missing_target(target_state)

        enemy_anchor = self._detect_anchor(image, anchor_template)
        if not enemy_anchor:
            return self._handle_missing_target(target_state)

        hud_template = self.templates.get("enemy_hud")
        if hud_template is None:
            return self._handle_missing_target(target_state)

        enemy_hud = self.resolver.resolve(enemy_anchor, hud_template)
        if not enemy_hud:
            return self._handle_missing_target(target_state)

        hud_image = self.resolver.crop(image, enemy_hud)
        if hud_image is None:
            return self._handle_missing_target(target_state)

        self.missing_hud_frames = 0
        target_state.reset(clear_selection=False)

        name_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_name"),
        )

        signature = self._create_signature(name_image)
        now = time.perf_counter()
        health_status, hp_percent = self._read_health_data(hud_image)

        if (
            not self.target_visible
            or self._signature_changed(signature)
        ):
            self._new_selection(signature, now)
        else:
            self.current_signature = signature

        self._update_health_tracking(
            health_status,
            hp_percent,
            now,
        )

        entity_type = self.current_entity_type

        target_state.selection_id = self.selection_id
        target_state.visible = True
        self._apply_health_state(
            target_state,
            health_status,
            now,
        )
        self._apply_cached_identity(
            target_state,
            signature,
        )

        if entity_type is None:
            target_state.identity_pending = False
        elif self.executor is None:
            if self._reserve_identity_attempt(now):
                self.read_identity(
                    hud_image,
                    target_state,
                    signature,
                    entity_type,
                )
        else:
            self._schedule_identity(
                hud_image,
                signature,
                entity_type,
                now,
            )
            target_state.identity_pending = (
                entity_type == self.ENTITY_ENEMY
                and self.recognized_entity_type is None
                and self.identity_attempts < self.MAX_IDENTITY_ATTEMPTS
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

        if not self._identity_is_current(
            selection_id,
            signature,
            name,
            entity_type,
        ):
            return

        try:
            committed = self._commit_identity(
                name,
                level,
                entity_type,
            )
        except Exception:
            return

        if committed is None:
            return

        name, level, entity_type = committed

        self._remember_identity(
            signature,
            name,
            level,
            entity_type,
        )

        target_state.identity_pending = False

        if (
            target_state.exists
            and entity_type == self.ENTITY_ENEMY
        ):
            target_state.name = name
            target_state.level = level

    def _target_missing(self):
        if not self.target_visible:
            return

        self.target_visible = False
        self.current_signature = None
        self.current_entity_type = None
        self._reset_health_tracking()
        self._reset_identity_attempts()
        self._clear_recognized_identity()
        self._clear_enemy_cache()

    def _handle_missing_target(self, target_state):
        if not self.target_visible:
            target_state.reset(clear_selection=False)
            return False

        self.missing_hud_frames += 1

        if self.missing_hud_frames < self.TARGET_MISS_CONFIRMATIONS:
            return False

        self.force_full_anchor_search = True
        self._target_missing()
        self.missing_hud_frames = 0
        target_state.reset(clear_selection=False)

        return False

    def _new_selection(self, signature, now):
        self.selection_id += 1
        self.target_visible = True
        self.current_signature = signature
        self.current_entity_type = None
        self._reset_health_tracking(started_at=now)
        self._reset_identity_attempts()
        self._clear_recognized_identity()
        self._clear_enemy_cache()

    def _reset_health_tracking(self, started_at=None):
        self.selection_started_at = started_at
        self.last_valid_hp = None
        self.last_valid_hp_at = None
        self.empty_hp_frames = 0
        self.health_dead = False
        self.empty_hp_started_at = None

    def _update_health_tracking(self, status, hp_percent, now):
        if status == self.HEALTH_MEASURED:
            self._set_entity_type(self.ENTITY_ENEMY)
            self.last_valid_hp = hp_percent
            self.last_valid_hp_at = now
            self.empty_hp_frames = 0
            self.empty_hp_started_at = None
            self.health_dead = False
            return

        if status == self.HEALTH_EMPTY:
            if self.current_entity_type == self.ENTITY_ENEMY:
                if self.empty_hp_frames == 0:
                    self.empty_hp_started_at = now

                self.empty_hp_frames += 1

                self.health_dead = (
                    self.last_valid_hp is not None
                    and self.empty_hp_frames >= self.HP_EMPTY_CONFIRMATIONS
                    and self.empty_hp_started_at is not None
                    and now - self.empty_hp_started_at
                    >= self.HP_EMPTY_CONFIRMATION_SECONDS
                )

            elif (
                self.current_entity_type is None
                and self._selection_age(now)
                >= self.HP_ACQUIRE_TIMEOUT_SECONDS
            ):
                self._set_entity_type(self.ENTITY_ITEM)

            return

        self.empty_hp_frames = 0
        self.empty_hp_started_at = None

    def _apply_health_state(self, target_state, status, now):
        target_state.hp_percent = float(
            self.last_valid_hp or 0.0
        )
        target_state.hp_observed_at = self.last_valid_hp_at

        if self.current_entity_type == self.ENTITY_ENEMY:
            target_state.exists = True
            target_state.targetable = not self.health_dead

            if self.health_dead:
                target_state.hp_percent = 0.0
                target_state.hp_valid = True
                target_state.hp_observed_at = now

            elif (
                status == self.HEALTH_MEASURED
                or self._last_hp_is_fresh(now)
            ):
                target_state.hp_valid = True

            return

        if self.current_entity_type == self.ENTITY_ITEM:
            return

        target_state.exists = True
        target_state.targetable = True

    def _last_hp_is_fresh(self, now):
        return bool(
            self.last_valid_hp is not None
            and self.last_valid_hp_at is not None
            and 0.0
            <= now - self.last_valid_hp_at
            <= self.HP_LAST_VALID_SECONDS
        )

    def _set_entity_type(self, entity_type):
        if entity_type == self.current_entity_type:
            return

        self.current_entity_type = entity_type
        self._clear_recognized_identity()

        if entity_type != self.ENTITY_ENEMY:
            self._clear_enemy_cache()

    def _selection_age(self, now):
        if self.selection_started_at is None:
            return 0.0

        return max(
            0.0,
            now - self.selection_started_at,
        )

    def _clear_recognized_identity(self):
        self.recognized_signature = None
        self.recognized_name = ""
        self.recognized_level = 0
        self.recognized_entity_type = None

    def _clear_enemy_cache(self):
        clear = getattr(
            self.entity_cache,
            "clear_enemy",
            None,
        )

        if callable(clear):
            clear()

    def _remember_identity(
        self,
        signature,
        name,
        level,
        entity_type,
    ):
        self.recognized_signature = signature
        self.recognized_name = name
        self.recognized_level = level
        self.recognized_entity_type = entity_type

    def _apply_cached_identity(
        self,
        target_state,
        signature,
    ):
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

    def _schedule_identity(
        self,
        hud_image,
        signature,
        entity_type,
        now=None,
    ):
        if (
            self.identity_future is not None
            or self.recognized_entity_type
        ):
            return

        if now is None:
            now = time.perf_counter()

        if not self._reserve_identity_attempt(now):
            return

        self.identity_future = self.executor.submit(
            self._read_identity_data,
            self.selection_id,
            signature,
            hud_image.copy(),
            entity_type,
        )

    def _reserve_identity_attempt(self, now):
        if (
            self.identity_attempts >= self.MAX_IDENTITY_ATTEMPTS
            or now < self.next_identity_retry_at
        ):
            return False

        self.identity_attempts += 1
        self.next_identity_retry_at = (
            now + self.IDENTITY_RETRY_SECONDS
        )

        return True

    def _reset_identity_attempts(self):
        self.identity_attempts = 0
        self.next_identity_retry_at = 0.0

    def _read_identity_data(
        self,
        selection_id,
        signature,
        hud_image,
        entity_type=ENTITY_ENEMY,
    ):
        empty_result = (
            selection_id,
            signature,
            None,
            0,
            None,
        )

        name_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_name"),
        )

        if name_image is None:
            return empty_result

        name = self.name_matcher.read_enemy_name(
            name_image
        )

        if not self.valid_name(name):
            return empty_result

        level = 0

        if entity_type == self.ENTITY_ENEMY:
            level_image = self.crop_region(
                hud_image,
                self.templates.get("enemy_level"),
            )

            level = (
                self.name_matcher.read_number(level_image)
                if level_image is not None
                else 0
            )

        return (
            selection_id,
            signature,
            name,
            level,
            entity_type,
        )

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

        selection_id, signature, name, level, resolved_type = (
            self._unpack_identity_result(result)
        )

        if not self._identity_is_current(
            selection_id,
            signature,
            name,
            resolved_type,
        ):
            return False

        committed = self._commit_identity(
            name,
            level,
            resolved_type,
        )

        if committed is None:
            return False

        name, level, resolved_type = committed

        self._remember_identity(
            signature,
            name,
            level,
            resolved_type,
        )

        target_state.identity_pending = False

        if (
            resolved_type == self.ENTITY_ENEMY
            and target_state.exists
        ):
            target_state.name = name
            target_state.level = level

        return resolved_type == self.ENTITY_ENEMY

    def _identity_is_current(
        self,
        selection_id,
        signature,
        name,
        entity_type,
    ):
        return bool(
            selection_id == self.selection_id
            and name
            and entity_type == self.current_entity_type
            and not self._signature_changed_from(
                signature,
                self.current_signature,
            )
        )

    def _commit_identity(
        self,
        name,
        level,
        entity_type,
    ):
        if entity_type == self.ENTITY_ITEM:
            resolver = getattr(
                self.entity_database,
                "resolve_item_name",
                None,
            )

            if not callable(resolver):
                return None

            resolved_name = resolver(name)

            if not resolved_name:
                return None

            register = getattr(
                self.entity_database,
                "register_item_seen",
                None,
            )

            if callable(register):
                register(resolved_name)

            return (
                resolved_name,
                0,
                self.ENTITY_ITEM,
            )

        resolver = getattr(
            self.entity_database,
            "resolve_enemy_name",
            None,
        )

        if not callable(resolver):
            return None

        resolved_name = resolver(name)

        if not resolved_name:
            return None

        if self.entity_cache.enemy_changed(
            resolved_name
        ):
            self.entity_cache.update_enemy(
                resolved_name,
                level,
            )
        else:
            level = self.entity_cache.current_enemy_level

        register = getattr(
            self.entity_database,
            "register_enemy_seen",
            None,
        )

        if callable(register):
            register(resolved_name)

        return (
            resolved_name,
            level,
            self.ENTITY_ENEMY,
        )

    def _detect_anchor(self, image, template):
        if not (
            isinstance(image, np.ndarray)
            and isinstance(
                getattr(template, "image", None),
                np.ndarray,
            )
        ):
            return self.detector.detect(
                image,
                template,
            )

        forced_search = self.force_full_anchor_search

        if not forced_search:
            detection = self._detect_cached_anchor(
                image,
                template,
            )

            if detection is not None:
                self.anchor_detection = detection
                self.last_anchor_confirmation_at = (
                    time.perf_counter()
                )
                return detection

        now = time.perf_counter()

        retry_seconds = (
            self.ANCHOR_RELOCATION_RETRY_SECONDS
            if self.anchor_detection is not None
            else self.ANCHOR_INITIAL_RETRY_SECONDS
        )

        if (
            not self.force_full_anchor_search
            and self.last_anchor_confirmation_at is not None
            and now - self.last_anchor_confirmation_at
            < retry_seconds
        ):
            return None

        self.last_anchor_confirmation_at = now

        detection = self._detect_in_search_area(
            image,
            template,
            "enemy_search_area",
        )

        if detection is not None:
            self.anchor_detection = detection
            self.force_full_anchor_search = False

        elif forced_search:
            self.anchor_detection = None
            self.force_full_anchor_search = False

        return detection

    def _detect_cached_anchor(
        self,
        image,
        template,
    ):
        cached = self.anchor_detection
        template_image = getattr(
            template,
            "image",
            None,
        )

        if (
            cached is None
            or not isinstance(image, np.ndarray)
            or not isinstance(template_image, np.ndarray)
            or image.ndim < 2
            or template_image.ndim < 2
        ):
            return None

        image_height, image_width = image.shape[:2]
        target_height, target_width = (
            template_image.shape[:2]
        )

        margin = self.ANCHOR_LOCAL_MARGIN

        left = max(
            0,
            int(cached["x"]) - margin,
        )

        top = max(
            0,
            int(cached["y"]) - margin,
        )

        right = min(
            image_width,
            int(cached["x"])
            + target_width
            + margin,
        )

        bottom = min(
            image_height,
            int(cached["y"])
            + target_height
            + margin,
        )

        search_image = image[
            top:bottom,
            left:right,
        ]

        detection = self.detector.detect(
            search_image,
            template,
        )

        if detection is None:
            return None

        detection = dict(detection)
        detection["x"] += left
        detection["y"] += top

        return detection

    def _detect_in_search_area(
        self,
        image,
        template,
        area_name,
    ):
        search_area = self.templates.get(area_name)

        # Si no hay una ROI configurada,
        # buscamos directamente en todo el frame.
        if search_area is None:
            return self.detector.detect(
                image,
                template,
            )

        search_image = self.resolver.crop(
            image,
            search_area,
        )

        # Si la ROI no se puede recortar,
        # usamos el frame completo.
        if search_image is None:
            return self.detector.detect(
                image,
                template,
            )

        # 1. Intento rápido en la posición habitual.
        detection = self.detector.detect(
            search_image,
            template,
        )

        if detection is not None:
            detection = dict(detection)

            detection["x"] += max(
                0,
                int(search_area["x"]),
            )

            detection["y"] += max(
                0,
                int(search_area["y"]),
            )

            return detection

        # 2. La ROI ha fallado.
        # Buscar el anchor del target en TODO el frame.
        #
        # De esta forma enemy_search_area es solamente
        # una optimización y no obliga al usuario a
        # mantener el HUD del target en una posición fija.
        detection = self.detector.detect(
            image,
            template,
        )

        if detection is not None:
            detection = dict(detection)

        return detection

    def _read_health_data(self, hud_image):
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("enemy_hp"),
        )

        if (
            not isinstance(hp_image, np.ndarray)
            or hp_image.size == 0
            or hp_image.ndim != 3
        ):
            return self.HEALTH_INVALID, None

        hp_percent = self.bar_reader.read_enemy_hp(
            hp_image
        )

        try:
            hp_percent = float(hp_percent)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            hp_percent = None

        if (
            hp_percent is not None
            and np.isfinite(hp_percent)
            and hp_percent > 0
        ):
            return (
                self.HEALTH_MEASURED,
                min(100.0, hp_percent),
            )

        if self.target_validator.has_red_bar(
            hp_image
        ):
            return self.HEALTH_INVALID, None

        return self.HEALTH_EMPTY, None

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
            and sum(
                character.isalpha()
                for character in normalized
            ) >= 2
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

        return image[
            y:y + height,
            x:x + width,
        ]

    def _signature_changed(self, signature):
        return self._signature_changed_from(
            signature,
            self.current_signature,
        )

    @classmethod
    def _signature_changed_from(
        cls,
        first,
        second,
    ):
        return bool(
            first is not None
            and second is not None
            and not cls._same_signature(
                first,
                second,
            )
        )

    @staticmethod
    def _create_signature(image):
        if (
            image is None
            or not isinstance(image, np.ndarray)
            or image.size == 0
        ):
            return None

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        resized = cv2.resize(
            gray,
            (32, 8),
            interpolation=cv2.INTER_AREA,
        )

        return resized >= 150

    @classmethod
    def _same_signature(
        cls,
        first,
        second,
    ):
        if (
            first is None
            or second is None
            or first.shape != second.shape
        ):
            return False

        return (
            float(np.mean(first != second))
            <= cls.SIGNATURE_DIFFERENCE
        )

    @classmethod
    def _unpack_identity_result(
        cls,
        result,
    ):
        if len(result) == 5:
            return result

        selection_id, signature, name, level = result

        return (
            selection_id,
            signature,
            name,
            level,
            cls.ENTITY_ENEMY,
        )