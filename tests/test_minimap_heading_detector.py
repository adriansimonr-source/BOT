import unittest
from unittest.mock import patch

import cv2
import numpy as np

from core.services.minimap_heading_detector import (
    HeadingDetection,
    MinimapHeadingDetector,
)


class MinimapHeadingDetectorTests(unittest.TestCase):

    @staticmethod
    def marker(angle):
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        center = np.array((25.0, 25.0))
        radians = np.radians(angle)
        direction = np.array((np.sin(radians), -np.cos(radians)))
        cv2.circle(image, (25, 25), 7, (0, 0, 230), -1)
        tip = tuple((center + direction * 10).astype(int))
        cv2.circle(image, tip, 3, (235, 245, 255), -1)
        return image

    def test_cardinal_and_diagonal_markers_need_two_matching_frames(self):
        for expected in (0, 45, 90, 180, 270, 315):
            with self.subTest(expected=expected):
                detector = MinimapHeadingDetector()
                image = self.marker(expected)

                self.assertIsNone(detector.update(image, 1.0))
                result = detector.update(image, 1.1)

                self.assertIsNotNone(result)
                error = abs((result.angle - expected + 180) % 360 - 180)
                self.assertLessEqual(error, 15)
                self.assertGreaterEqual(result.confidence, 0.55)

    def test_red_distractor_does_not_replace_the_central_marker(self):
        detector = MinimapHeadingDetector()
        image = self.marker(90)
        cv2.rectangle(image, (1, 1), (6, 6), (0, 0, 255), -1)

        first = detector.detect(image, 1.0)

        self.assertIsNotNone(first)
        self.assertLessEqual(abs(first.angle - 90), 15)

    def test_body_without_a_light_tip_is_invalid(self):
        detector = MinimapHeadingDetector()
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.circle(image, (25, 25), 7, (0, 0, 230), -1)

        self.assertIsNone(detector.detect(image, 1.0))

    def test_large_white_icon_next_to_body_is_not_a_tip(self):
        detector = MinimapHeadingDetector()
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.circle(image, (25, 25), 7, (0, 0, 230), -1)
        cv2.rectangle(image, (31, 14), (43, 24), (245, 245, 245), -1)

        self.assertIsNone(detector.detect(image, 1.0))

    def test_large_white_distractor_does_not_replace_valid_tip(self):
        detector = MinimapHeadingDetector()
        image = self.marker(90)
        cv2.rectangle(image, (10, 13), (20, 22), (245, 245, 245), -1)

        result = detector.detect(image, 1.0)

        self.assertIsNotNone(result)
        self.assertLessEqual(abs(result.angle - 90), 15)

    def test_distant_compact_white_dot_is_not_a_tip(self):
        detector = MinimapHeadingDetector()
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.circle(image, (25, 25), 7, (0, 0, 230), -1)
        cv2.circle(image, (25, 6), 3, (245, 245, 245), -1)

        self.assertIsNone(detector.detect(image, 1.0))

    def test_elongated_white_shape_is_not_a_tip(self):
        detector = MinimapHeadingDetector()
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.circle(image, (25, 25), 7, (0, 0, 230), -1)
        cv2.rectangle(image, (31, 17), (33, 29), (245, 245, 245), -1)

        self.assertIsNone(detector.detect(image, 1.0))

    def test_circular_filter_accepts_wraparound_and_rejects_opposite_outlier(self):
        detector = MinimapHeadingDetector()
        samples = iter(
            (
                HeadingDetection(359, 0.9, 1.0),
                HeadingDetection(1, 0.9, 1.1),
                HeadingDetection(180, 0.9, 1.2),
            )
        )
        with patch.object(detector, "detect", side_effect=lambda *_: next(samples)):
            self.assertIsNone(detector.update(object(), 1.0))
            result = detector.update(object(), 1.1)
            filtered = detector.update(object(), 1.2)

        self.assertLess(min(result.angle, 360 - result.angle), 2)
        self.assertLess(min(filtered.angle, 360 - filtered.angle), 2)

    def test_same_frame_timestamp_cannot_confirm_a_heading(self):
        detector = MinimapHeadingDetector()
        image = self.marker(90)

        self.assertIsNone(detector.update(image, 1.0))
        self.assertIsNone(detector.update(image, 1.0))

    def test_filter_rejects_a_group_with_excessive_pairwise_spread(self):
        detector = MinimapHeadingDetector()
        samples = iter(
            (
                HeadingDetection(0, 0.9, 1.0),
                HeadingDetection(20, 0.9, 1.1),
                HeadingDetection(40, 0.9, 1.2),
            )
        )
        with patch.object(detector, "detect", side_effect=lambda *_: next(samples)):
            detector.update(object(), 1.0)
            detector.update(object(), 1.1)
            result = detector.update(object(), 1.2)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
