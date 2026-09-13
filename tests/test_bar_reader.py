import unittest

import numpy as np

from core.services.bar_reader import BarReader


class BarReaderTests(unittest.TestCase):

    def setUp(self):
        self.reader = BarReader()

    @staticmethod
    def bar(width, fill, color):
        image = np.zeros(
            (10, width, 3),
            dtype=np.uint8,
        )
        image[:, :fill] = color
        return image

    def test_player_hp_reads_full_and_partial_red_bars(self):
        full = self.bar(
            255,
            215,
            (0, 0, 200),
        )

        half = self.bar(
            255,
            108,
            (0, 0, 200),
        )

        self.assertEqual(
            self.reader.read_hp(full),
            100.0,
        )

        self.assertAlmostEqual(
            self.reader.read_hp(half),
            50.23,
            places=2,
        )

    def test_player_mp_reads_a_partial_blue_bar(self):
        image = self.bar(
            258,
            107,
            (200, 0, 0),
        )

        self.assertEqual(
            self.reader.read_mp(image),
            50.0,
        )

    def test_enemy_hp_reads_full_bar(self):
        image = self.bar(
            259,
            214,
            (0, 0, 200),
        )

        self.assertEqual(
            self.reader.read_enemy_hp(image),
            100.0,
        )

    def test_empty_enemy_bar_is_unknown_instead_of_zero_hp(self):
        image = self.bar(
            259,
            0,
            (0, 0, 200),
        )

        self.assertIsNone(
            self.reader.read_enemy_hp(image)
        )

    def test_sparse_color_noise_is_not_counted_as_a_bar(self):
        image = np.zeros(
            (10, 255, 3),
            dtype=np.uint8,
        )

        image[:2, :100] = (
            0,
            0,
            200,
        )

        self.assertIsNone(
            self.reader.read_hp(image)
        )

    def test_invalid_images_return_an_empty_reading(self):
        self.assertIsNone(
            self.reader.read_hp(None)
        )

        self.assertIsNone(
            self.reader.read_hp(
                np.zeros(
                    (10, 10),
                    dtype=np.uint8,
                )
            )
        )

        self.assertIsNone(
            self.reader.read_mp(
                np.empty(
                    (0, 0, 3),
                    dtype=np.uint8,
                )
            )
        )

    def test_dim_dominant_resource_colors_remain_measurable(self):
        hp = self.bar(
            255,
            54,
            (25, 30, 90),
        )

        mp = self.bar(
            258,
            107,
            (90, 30, 25),
        )

        self.assertAlmostEqual(
            self.reader.read_hp(hp),
            25.12,
            places=2,
        )

        self.assertEqual(
            self.reader.read_mp(mp),
            50.0,
        )

    def test_neutral_bright_pixels_are_not_resource_fill(self):
        image = self.bar(
            255,
            100,
            (180, 180, 180),
        )

        self.assertIsNone(
            self.reader.read_hp(image)
        )

        self.assertIsNone(
            self.reader.read_mp(image)
        )

    def test_player_hp_scales_with_crop_width(self):
        full = self.bar(
            128,
            108,
            (0, 0, 200),
        )

        half = self.bar(
            128,
            54,
            (0, 0, 200),
        )

        self.assertEqual(
            self.reader.read_hp(full),
            100.0,
        )

        self.assertAlmostEqual(
            self.reader.read_hp(half),
            50.0,
            delta=1.0,
        )

    def test_player_mp_scales_with_crop_width(self):
        full = self.bar(
            129,
            107,
            (200, 0, 0),
        )

        half = self.bar(
            129,
            54,
            (200, 0, 0),
        )

        self.assertEqual(
            self.reader.read_mp(full),
            100.0,
        )

        self.assertAlmostEqual(
            self.reader.read_mp(half),
            50.0,
            delta=1.0,
        )

    def test_enemy_hp_scales_with_crop_width(self):
        full = self.bar(
            130,
            107,
            (0, 0, 200),
        )

        half = self.bar(
            130,
            54,
            (0, 0, 200),
        )

        self.assertEqual(
            self.reader.read_enemy_hp(full),
            100.0,
        )

        self.assertAlmostEqual(
            self.reader.read_enemy_hp(half),
            50.0,
            delta=1.0,
        )


if __name__ == "__main__":
    unittest.main()