import unittest
from types import SimpleNamespace

import numpy as np

from core.services.hud_resolver import HUDResolver
from core.services.template_detector import TemplateDetector


class TemplateDetectorTests(unittest.TestCase):

    @staticmethod
    def template(image, threshold=0.9):
        return SimpleNamespace(
            image=image,
            threshold=threshold,
            name="anchor",
            type="anchor",
        )

    def test_detect_returns_the_best_match(self):
        pattern = np.array(
            [[0, 20, 40], [60, 90, 120], [150, 200, 255]],
            dtype=np.uint8,
        )
        image = np.zeros((9, 11), dtype=np.uint8)
        image[4:7, 6:9] = pattern

        match = TemplateDetector.detect(image, self.template(pattern))

        self.assertEqual((match["x"], match["y"]), (6, 4))
        self.assertEqual((match["width"], match["height"]), (3, 3))
        self.assertEqual(match["confidence"], 1.0)

    def test_detect_rejects_a_match_below_threshold(self):
        pattern = np.array(
            [[0, 20, 40], [60, 90, 120], [150, 200, 255]],
            dtype=np.uint8,
        )
        image = np.zeros((9, 11), dtype=np.uint8)

        self.assertIsNone(
            TemplateDetector.detect(image, self.template(pattern, 0.9))
        )

    def test_detect_rejects_a_template_larger_than_the_image(self):
        image = np.zeros((2, 2), dtype=np.uint8)
        template = np.zeros((3, 3), dtype=np.uint8)

        self.assertIsNone(
            TemplateDetector.detect(image, self.template(template))
        )


class HUDResolverTests(unittest.TestCase):

    def test_crop_clamps_negative_and_overflowing_bounds(self):
        image = np.arange(30).reshape(5, 6)

        top_left = HUDResolver.crop(
            image,
            {"x": -2, "y": -1, "width": 5, "height": 4},
        )
        bottom_right = HUDResolver.crop(
            image,
            {"x": 4, "y": 3, "width": 5, "height": 4},
        )

        np.testing.assert_array_equal(top_left, image[0:3, 0:3])
        np.testing.assert_array_equal(bottom_right, image[3:5, 4:6])

    def test_crop_rejects_regions_outside_the_image(self):
        image = np.zeros((5, 6), dtype=np.uint8)

        self.assertIsNone(
            HUDResolver.crop(
                image,
                {"x": 8, "y": 8, "width": 2, "height": 2},
            )
        )
        self.assertIsNone(
            HUDResolver.crop(
                image,
                {"x": 1, "y": 1, "width": 0, "height": 2},
            )
        )


if __name__ == "__main__":
    unittest.main()
