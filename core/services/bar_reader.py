import cv2
import numpy as np


class BarReader:
    FULL_WIDTHS = {
        "player_hp": 245,
        "player_mp": 244,
        "enemy_hp": 233,
    }
    MIN_COLOR_VALUE = 70
    MIN_COLOR_DOMINANCE = 25
    MIN_BAR_WIDTH = 2

    def read_hp(self, image):
        return self.read_bar(image, "red", "player_hp")

    def read_mp(self, image):
        return self.read_bar(image, "blue", "player_mp")

    def read_enemy_hp(self, image):
        return self.read_bar(image, "red", "enemy_hp")

    def read_bar(self, image, color, bar_type):
        if (
            not isinstance(image, np.ndarray)
            or image.size == 0
            or image.ndim != 3
            or image.shape[2] < 3
        ):
            return None

        mask = self.create_mask(image, color)
        minimum_height = max(1, int(image.shape[0] * 0.30))
        active_columns = (
            np.count_nonzero(mask, axis=0) >= minimum_height
        )
        detected_width = self._longest_active_span(active_columns)
        if detected_width < self.MIN_BAR_WIDTH:
            return None

        full_width = self.FULL_WIDTHS.get(bar_type, detected_width)
        percentage = min(100.0, detected_width / full_width * 100)
        if percentage >= 96:
            percentage = 100.0
        return round(percentage, 2)

    @classmethod
    def create_mask(cls, image, color):
        blue = image[:, :, 0].astype(np.int16)
        green = image[:, :, 1].astype(np.int16)
        red = image[:, :, 2].astype(np.int16)
        if color == "red":
            other = np.maximum(green, blue)
            return (
                (red >= cls.MIN_COLOR_VALUE)
                & (red - other >= cls.MIN_COLOR_DOMINANCE)
            )
        if color == "blue":
            other = np.maximum(green, red)
            return (
                (blue >= cls.MIN_COLOR_VALUE)
                & (blue - other >= cls.MIN_COLOR_DOMINANCE)
            )
        return np.zeros(image.shape[:2], dtype=bool)

    @staticmethod
    def _longest_active_span(active_columns, tolerated_gap=2):
        longest = 0
        current = 0
        gap = 0
        for active in active_columns:
            if active:
                current += gap + 1
                gap = 0
                longest = max(longest, current)
            elif current and gap < tolerated_gap:
                gap += 1
            else:
                current = 0
                gap = 0
        return longest

    @classmethod
    def create_structure_mask(cls, image):
        if (
            not isinstance(image, np.ndarray)
            or image.size == 0
            or image.ndim != 3
            or image.shape[2] < 3
        ):
            return None
        dynamic = cls.create_mask(image, "red") | cls.create_mask(
            image,
            "blue",
        )
        if not np.any(dynamic):
            return None
        expanded = cv2.dilate(
            dynamic.astype(np.uint8),
            np.ones((7, 7), dtype=np.uint8),
        ).astype(bool)
        structure = expanded & ~dynamic
        if np.count_nonzero(structure) < 32:
            return None
        return structure.astype(np.uint8) * 255
