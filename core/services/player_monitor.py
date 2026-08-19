import time

import numpy as np

from core.models.player_state import PlayerState


class PlayerMonitor:

    RESOURCE_REACQUIRE_AFTER_MISSES = 4
    SINGLE_RESOURCE_REACQUIRE_AFTER_MISSES = 8
    ANCHOR_LOCAL_MARGIN = 24
    ANCHOR_FULL_RETRY_SECONDS = 0.5

    def __init__(self, detector, resolver, bar_reader, templates):
        self.detector = detector
        self.resolver = resolver
        self.bar_reader = bar_reader
        self.templates = templates
        self.player_hud = None
        self.anchor_detection = None
        self.last_full_anchor_search_at = None
        self.hp_misses = 0
        self.mp_misses = 0

    def update(self, image, player_state: PlayerState):
        if image is None:
            return False

        if self.player_hud is not None:
            hud_image = self._crop_hud(image, self.player_hud)
            if hud_image is not None:
                resource_status = self.read_resources(
                    hud_image,
                    player_state,
                )
                if not self._reacquire_due(resource_status):
                    return any(resource_status)
                self._reset_resource_misses()
            else:
                self.player_hud = None
                self._reset_resource_misses()

        anchor_template = self.templates.get("player_anchor")
        if anchor_template is None:
            return False

        player_anchor = self._detect_anchor(image, anchor_template)
        if not player_anchor:
            return False

        hud_template = self.templates.get("player_hud")
        if hud_template is None:
            return False

        player_hud = self.resolver.resolve(player_anchor, hud_template)
        if not player_hud:
            return False

        hud_image = self._crop_hud(image, player_hud)
        if hud_image is None:
            return False

        self.player_hud = player_hud
        self._reset_resource_misses()

        resource_status = self.read_resources(
            hud_image,
            player_state,
        )
        self._record_resource_status(resource_status)

        return any(resource_status)

    def read_resources(self, hud_image, player_state):
        observed_at = time.perf_counter()

        hp_updated = False
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("player_hp"),
        )

        if hp_image is not None:
            hp_percent = self.bar_reader.read_hp(hp_image)
            if hp_percent is not None:
                hp_updated = player_state.update_hp(
                    hp_percent,
                    observed_at=observed_at,
                )

        mp_updated = False
        mp_image = self.crop_region(
            hud_image,
            self.templates.get("player_mp"),
        )

        if mp_image is not None:
            mp_percent = self.bar_reader.read_mp(mp_image)
            if mp_percent is not None:
                mp_updated = player_state.update_mp(
                    mp_percent,
                    observed_at=observed_at,
                )

        return hp_updated, mp_updated

    def _reacquire_due(self, resource_status):
        self._record_resource_status(resource_status)

        hp_updated, mp_updated = resource_status

        if not hp_updated and not mp_updated:
            return max(
                self.hp_misses,
                self.mp_misses,
            ) >= self.RESOURCE_REACQUIRE_AFTER_MISSES

        return bool(
            (
                not hp_updated
                and self.hp_misses
                >= self.SINGLE_RESOURCE_REACQUIRE_AFTER_MISSES
            )
            or
            (
                not mp_updated
                and self.mp_misses
                >= self.SINGLE_RESOURCE_REACQUIRE_AFTER_MISSES
            )
        )

    def _record_resource_status(self, resource_status):
        hp_updated, mp_updated = resource_status

        self.hp_misses = (
            0
            if hp_updated
            else self.hp_misses + 1
        )

        self.mp_misses = (
            0
            if mp_updated
            else self.mp_misses + 1
        )

    def _reset_resource_misses(self):
        self.hp_misses = 0
        self.mp_misses = 0

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

        detection = self._detect_cached_anchor(
            image,
            template,
        )

        if detection is None:
            now = time.perf_counter()

            if (
                self.last_full_anchor_search_at is not None
                and now - self.last_full_anchor_search_at
                < self.ANCHOR_FULL_RETRY_SECONDS
            ):
                return None

            detection = self._detect_in_search_area(
                image,
                template,
                "player_search_area",
            )

            self.last_full_anchor_search_at = time.perf_counter()

        if detection is not None:
            self.anchor_detection = detection

        return detection

    def _detect_cached_anchor(self, image, template):
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
        target_height, target_width = template_image.shape[:2]

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

        detection = self.detector.detect(
            image[
                top:bottom,
                left:right,
            ],
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

        # Si no hay ROI configurada,
        # buscar directamente en todo el frame.
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
        # buscar también en todo el frame.
        if search_image is None:
            return self.detector.detect(
                image,
                template,
            )

        # 1. Búsqueda rápida en la ROI habitual.
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

        # 2. Si no está en la ROI,
        # buscar en toda la pantalla.
        #
        # Esto permite mover el HUD del jugador
        # sin que el bot deje de localizarlo.
        detection = self.detector.detect(
            image,
            template,
        )

        if detection is not None:
            detection = dict(detection)

        return detection

    def _crop_hud(self, image, hud):
        crop = self.resolver.crop(
            image,
            hud,
        )

        if crop is None:
            return None

        if isinstance(hud, dict):
            expected_height = max(
                0,
                int(hud.get("height", 0)),
            )

            expected_width = max(
                0,
                int(hud.get("width", 0)),
            )

            if crop.shape[:2] != (
                expected_height,
                expected_width,
            ):
                return None

        return crop

    @staticmethod
    def crop_region(image, region):
        if (
            image is None
            or region is None
            or not hasattr(image, "shape")
        ):
            return None

        x = int(region.get("x", 0))
        y = int(region.get("y", 0))
        width = int(region.get("width", 0))
        height = int(region.get("height", 0))

        image_height, image_width = image.shape[:2]

        if (
            x < 0
            or y < 0
            or width <= 0
            or height <= 0
            or x + width > image_width
            or y + height > image_height
        ):
            return None

        return image[
            y:y + height,
            x:x + width,
        ]