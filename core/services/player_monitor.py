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
                    scale=self._region_scale(self.player_hud),
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

        player_anchor = self._detect_anchor(
            image,
            anchor_template,
        )

        if not player_anchor:
            return False

        hud_template = self.templates.get("player_hud")

        if hud_template is None:
            return False

        player_hud = self.resolver.resolve(
            player_anchor,
            hud_template,
        )

        if not player_hud:
            return False

        hud_image = self._crop_hud(
            image,
            player_hud,
        )

        if hud_image is None:
            return False

        self.player_hud = player_hud
        self._reset_resource_misses()

        resource_status = self.read_resources(
            hud_image,
            player_state,
            scale=self._region_scale(player_hud),
        )

        self._record_resource_status(resource_status)

        return any(resource_status)

    def read_resources(
        self,
        hud_image,
        player_state,
        scale=1.0,
    ):
        observed_at = time.perf_counter()

        hp_updated = False
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("player_hp"),
            scale=scale,
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
            scale=scale,
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

        scale = self._cached_scale()

        image_height, image_width = image.shape[:2]

        target_height = max(
            1,
            int(round(template_image.shape[0] * scale)),
        )

        target_width = max(
            1,
            int(round(template_image.shape[1] * scale)),
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

        detection = self.detector.detect(
            image[top:bottom, left:right],
            template,
            scale_hint=scale,
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
        scale_hint = self._cached_scale_or_none()

        if search_area is None:
            return self.detector.detect(
                image,
                template,
                scale_hint=scale_hint,
            )

        search_image = self.resolver.crop(
            image,
            search_area,
        )

        if search_image is None:
            return self.detector.detect(
                image,
                template,
                scale_hint=scale_hint,
            )

        detection = self.detector.detect(
            search_image,
            template,
            scale_hint=scale_hint,
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

        return self.detector.detect(
            image,
            template,
            scale_hint=scale_hint,
        )

    def _cached_scale(self):
        scale = self._cached_scale_or_none()
        return 1.0 if scale is None else scale

    def _cached_scale_or_none(self):
        if not isinstance(self.anchor_detection, dict):
            return None

        return self._region_scale(
            self.anchor_detection,
            default=None,
        )

    @staticmethod
    def _region_scale(region, default=1.0):
        if not isinstance(region, dict):
            return default

        try:
            scale = float(
                region.get(
                    "scale",
                    1.0 if default is None else default,
                )
            )
        except (TypeError, ValueError, OverflowError):
            return default

        if not np.isfinite(scale) or scale <= 0:
            return default

        return scale

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
    def crop_region(
        image,
        region,
        scale=1.0,
    ):
        if (
            image is None
            or region is None
            or not hasattr(image, "shape")
        ):
            return None

        try:
            scale = float(scale)
        except (TypeError, ValueError, OverflowError):
            scale = 1.0

        if not np.isfinite(scale) or scale <= 0:
            scale = 1.0

        x = int(round(region.get("x", 0) * scale))
        y = int(round(region.get("y", 0) * scale))
        width = int(round(region.get("width", 0) * scale))
        height = int(round(region.get("height", 0) * scale))

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