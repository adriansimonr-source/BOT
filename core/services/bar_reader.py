import cv2
import numpy as np


class BarReader:

    BAR_WIDTH_RATIOS = {
        "player_hp": 215.0 / 255.0,
        "player_mp": 214.0 / 258.0,
        "enemy_hp": 214.0 / 259.0,
    }

    MIN_COLOR_VALUE = 70
    MIN_COLOR_DOMINANCE = 25
    MIN_BAR_WIDTH = 2
    FULL_THRESHOLD = 96.0

    def read_hp(self, image, scale=1.0):
        return self.read_bar(
            image,
            "red",
            "player_hp",
        )

    def read_mp(self, image, scale=1.0):
        return self.read_bar(
            image,
            "blue",
            "player_mp",
        )

    def read_enemy_hp(self, image, scale=1.0):
        return self.read_bar(
            image,
            "red",
            "enemy_hp",
        )

    def read_bar(
        self,
        image,
        color,
        bar_type,
        scale=1.0,
    ):
        if not self._valid_image(image):
            return None

        mask = self.create_mask(
            image,
            color,
        )

        minimum_height = max(
            1,
            int(round(image.shape[0] * 0.30)),
        )

        active_columns = (
            np.count_nonzero(
                mask,
                axis=0,
            )
            >= minimum_height
        )

        detected_width = self._longest_active_span(
            active_columns
        )

        if detected_width < self.MIN_BAR_WIDTH:
            return None

        full_width = self._get_full_width(
            image,
            bar_type,
        )

        if full_width <= 0:
            return None

        percentage = (
            float(detected_width)
            / float(full_width)
            * 100.0
        )

        percentage = min(
            100.0,
            max(
                0.0,
                percentage,
            ),
        )

        if percentage >= self.FULL_THRESHOLD:
            percentage = 100.0

        return round(
            percentage,
            2,
        )

    @classmethod
    def _get_full_width(
        cls,
        image,
        bar_type,
    ):
        ratio = cls.BAR_WIDTH_RATIOS.get(
            bar_type
        )

        if ratio is None:
            return float(
                image.shape[1]
            )

        return max(
            1.0,
            float(image.shape[1]) * ratio,
        )

    @classmethod
    def create_mask(
        cls,
        image,
        color,
    ):
        if not cls._valid_image(image):
            return np.zeros(
                (0, 0),
                dtype=bool,
            )

        blue = image[:, :, 0].astype(
            np.int16,
            copy=False,
        )

        green = image[:, :, 1].astype(
            np.int16,
            copy=False,
        )

        red = image[:, :, 2].astype(
            np.int16,
            copy=False,
        )

        if color == "red":
            other = np.maximum(
                green,
                blue,
            )

            return (
                (red >= cls.MIN_COLOR_VALUE)
                & (
                    red - other
                    >= cls.MIN_COLOR_DOMINANCE
                )
            )

        if color == "blue":
            other = np.maximum(
                green,
                red,
            )

            return (
                (blue >= cls.MIN_COLOR_VALUE)
                & (
                    blue - other
                    >= cls.MIN_COLOR_DOMINANCE
                )
            )

        return np.zeros(
            image.shape[:2],
            dtype=bool,
        )

    @staticmethod
    def _longest_active_span(
        active_columns,
        tolerated_gap=2,
    ):
        longest = 0
        current = 0
        gap = 0

        for active in active_columns:
            if active:
                current += gap + 1
                gap = 0

                if current > longest:
                    longest = current

            elif current and gap < tolerated_gap:
                gap += 1

            else:
                current = 0
                gap = 0

        return longest

    @classmethod
    def create_structure_mask(
        cls,
        image,
    ):
        if not cls._valid_image(image):
            return None

        dynamic = (
            cls.create_mask(
                image,
                "red",
            )
            | cls.create_mask(
                image,
                "blue",
            )
        )

        if not np.any(dynamic):
            return None

        kernel = np.ones(
            (7, 7),
            dtype=np.uint8,
        )

        expanded = cv2.dilate(
            dynamic.astype(
                np.uint8,
                copy=False,
            ),
            kernel,
        ).astype(bool)

        structure = (
            expanded
            & ~dynamic
        )

        if np.count_nonzero(structure) < 32:
            return None

        return (
            structure.astype(
                np.uint8,
                copy=False,
            )
            * 255
        )

    @staticmethod
    def _valid_image(image):
        return bool(
            isinstance(
                image,
                np.ndarray,
            )
            and image.size > 0
            and image.ndim == 3
            and image.shape[2] >= 3
            and image.shape[0] > 0
            and image.shape[1] > 0
        )