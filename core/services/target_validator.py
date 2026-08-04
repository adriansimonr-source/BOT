import cv2
import numpy as np


class TargetValidator:

    MIN_BAR_HEIGHT_RATIO = 0.25
    MIN_BAR_WIDTH_RATIO = 0.008

    def validate_enemy(self, hud_image, hp_image=None):
        health_region = hp_image if hp_image is not None else hud_image
        return (
            self.has_red_bar(health_region)
            and not self.has_blue_bar(hud_image)
        )

    def has_red_bar(self, image):
        if not self._is_valid_image(image):
            return False

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        first = cv2.inRange(
            hsv,
            np.array([0, 80, 80]),
            np.array([10, 255, 255]),
        )
        second = cv2.inRange(
            hsv,
            np.array([170, 80, 80]),
            np.array([180, 255, 255]),
        )
        return self._has_horizontal_bar(first | second)

    def has_blue_bar(self, image):
        if not self._is_valid_image(image):
            return False

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv,
            np.array([90, 60, 50]),
            np.array([140, 255, 255]),
        )
        return self._has_horizontal_bar(mask)

    @staticmethod
    def _is_valid_image(image):
        return bool(
            isinstance(image, np.ndarray)
            and image.size
            and image.ndim == 3
            and image.shape[2] >= 3
        )

    @classmethod
    def _has_horizontal_bar(cls, mask):
        if mask is None or not getattr(mask, "size", 0):
            return False

        height, width = mask.shape[:2]
        minimum_height = max(1, int(np.ceil(height * cls.MIN_BAR_HEIGHT_RATIO)))
        minimum_width = max(2, int(round(width * cls.MIN_BAR_WIDTH_RATIO)))
        active_columns = np.count_nonzero(mask, axis=0) >= minimum_height

        longest_run = 0
        current_run = 0
        for active in active_columns:
            current_run = current_run + 1 if active else 0
            longest_run = max(longest_run, current_run)
            if longest_run >= minimum_width:
                return True
        return False
