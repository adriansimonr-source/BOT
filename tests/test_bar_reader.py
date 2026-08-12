import unittest

import numpy as np

from core.services.bar_reader import BarReader


class BarReaderTests(unittest.TestCase):
    def setUp(self):
        self.reader = BarReader()

    @staticmethod
    def bar(width, fill, color):
        image = np.zeros((10, width, 3), dtype=np.uint8)
        image[:, :fill] = color
        return image

    def test_player_hp_reads_full_and_partial_red_bars(self):
        full = self.bar(245, 245, (0, 0, 200))
        half = self.bar(245, 122, (0, 0, 200))

        self.assertEqual(self.reader.read_hp(full), 100.0)
        self.assertEqual(self.reader.read_hp(half), 49.8)

    def test_player_mp_reads_a_partial_blue_bar(self):
        image = self.bar(244, 61, (200, 0, 0))

        self.assertEqual(self.reader.read_mp(image), 25.0)

    def test_empty_enemy_bar_is_unknown_instead_of_zero_hp(self):
        image = self.bar(233, 0, (0, 0, 200))

        self.assertIsNone(self.reader.read_enemy_hp(image))

    def test_sparse_color_noise_is_not_counted_as_a_bar(self):
        image = np.zeros((10, 245, 3), dtype=np.uint8)
        image[:2, :100] = (0, 0, 200)

        self.assertEqual(self.reader.read_hp(image), 0)

    def test_invalid_images_return_an_empty_reading(self):
        self.assertEqual(self.reader.read_hp(None), 0)
        self.assertEqual(self.reader.read_hp(np.zeros((10, 10))), 0)
        self.assertEqual(
            self.reader.read_mp(np.empty((0, 0, 3), dtype=np.uint8)),
            0,
        )


if __name__ == "__main__":
    unittest.main()
