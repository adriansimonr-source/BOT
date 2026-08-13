import time

from core.models.player_state import PlayerState


class PlayerMonitor:
    def __init__(self, detector, resolver, bar_reader, templates):
        self.detector = detector
        self.resolver = resolver
        self.bar_reader = bar_reader
        self.templates = templates

    def update(self, image, player_state: PlayerState):
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
        return True

    def read_resources(self, hud_image, player_state):
        observed_at = time.perf_counter()
        hp_image = self.crop_region(
            hud_image,
            self.templates.get("player_hp"),
        )
        if hp_image is not None:
            player_state.update_hp(
                self.bar_reader.read_hp(hp_image),
                observed_at=observed_at,
            )

        mp_image = self.crop_region(
            hud_image,
            self.templates.get("player_mp"),
        )
        if mp_image is not None:
            player_state.update_mp(
                self.bar_reader.read_mp(mp_image),
                observed_at=observed_at,
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
