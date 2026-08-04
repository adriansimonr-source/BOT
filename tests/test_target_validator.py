import unittest

import numpy as np

from core.services.target_validator import TargetValidator


class TargetValidatorTests(unittest.TestCase):

    def setUp(self):
        self.validator = TargetValidator()

    def test_short_low_hp_fill_is_still_a_bar(self):
        image = np.zeros((19, 259, 3), dtype=np.uint8)
        image[4:15, 20:22] = (0, 0, 220)

        self.assertTrue(self.validator.has_red_bar(image))

    def test_isolated_red_noise_is_not_a_bar(self):
        image = np.zeros((19, 259, 3), dtype=np.uint8)
        image[4:15, 20] = (0, 0, 220)
        image[4:15, 40] = (0, 0, 220)

        self.assertFalse(self.validator.has_red_bar(image))

    def test_missing_or_invalid_image_has_no_bar(self):
        self.assertFalse(self.validator.has_red_bar(None))
        self.assertFalse(
            self.validator.has_red_bar(np.zeros((0, 0, 3), dtype=np.uint8))
        )


if __name__ == "__main__":
    unittest.main()
