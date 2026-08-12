import numpy as np


class BarReader:
    FULL_WIDTHS = {
        "player_hp": 245,
        "player_mp": 244,
        "enemy_hp": 233,
    }
    RED_THRESHOLD = (120, 120, 130)
    BLUE_THRESHOLD = (100, 170, 170)

    def read_hp(self, image):
        return self.read_bar(image, "red", "player_hp")

    def read_mp(self, image):
        return self.read_bar(image, "blue", "player_mp")

    def read_enemy_hp(self, image):
        percentage = self.read_bar(image, "red", "enemy_hp")
        return percentage if percentage > 0 else None

    def read_bar(self, image, color, bar_type):
        if (
            not isinstance(image, np.ndarray)
            or image.size == 0
            or image.ndim != 3
            or image.shape[2] < 3
        ):
            return 0

        mask = self.create_mask(image, color)
        minimum_height = max(1, int(image.shape[0] * 0.30))
        detected_width = int(
            np.count_nonzero(np.sum(mask, axis=0) >= minimum_height)
        )
        if detected_width == 0:
            return 0

        full_width = self.FULL_WIDTHS.get(bar_type, detected_width)
        percentage = min(100.0, detected_width / full_width * 100)
        if percentage >= 96:
            percentage = 100.0
        return round(percentage, 2)

    @classmethod
    def create_mask(cls, image, color):
        blue, green, red = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        if color == "red":
            max_blue, max_green, min_red = cls.RED_THRESHOLD
            return (red > min_red) & (green < max_green) & (blue < max_blue)
        if color == "blue":
            min_blue, max_green, max_red = cls.BLUE_THRESHOLD
            return (blue > min_blue) & (green < max_green) & (red < max_red)
        return np.zeros(image.shape[:2], dtype=bool)
