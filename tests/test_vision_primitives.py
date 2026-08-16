import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from core.services.hud_resolver import HUDResolver
from core.services.bar_reader import BarReader
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

    @staticmethod
    def load_image(path):
        encoded = np.frombuffer(Path(path).read_bytes(), dtype=np.uint8)
        return cv2.imdecode(encoded, cv2.IMREAD_COLOR)

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

    def test_masked_detection_ignores_a_changed_resource_fill(self):
        generator = np.random.default_rng(7)
        template_image = generator.integers(
            15,
            70,
            size=(20, 30, 3),
            dtype=np.uint8,
        )
        template_image[5:15, 8:25] = (10, 15, 210)
        changed = template_image.copy()
        changed[5:15, 16:25] = (30, 35, 40)
        source = np.zeros((35, 50, 3), dtype=np.uint8)
        source[9:29, 11:41] = changed
        mask = BarReader.create_structure_mask(template_image)

        match = TemplateDetector.detect_masked(
            source,
            self.template(template_image, 0.95),
            mask,
        )

        self.assertEqual((match["x"], match["y"]), (11, 9))
        self.assertGreaterEqual(match["confidence"], 0.99)

    def test_real_masked_anchors_reject_uniform_and_noisy_frames(self):
        anchor_dir = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "templates"
            / "anchors"
        )
        generator = np.random.default_rng(11)
        uniform = np.full((640, 640, 3), 60, dtype=np.uint8)
        noise = generator.integers(
            0,
            256,
            size=(640, 640, 3),
            dtype=np.uint8,
        )

        for filename, threshold in (
            ("enemy_anchor.png", 0.75),
            ("player_anchor.png", 0.90),
        ):
            image = self.load_image(anchor_dir / filename)
            template = self.template(image, threshold)
            mask = BarReader.create_structure_mask(image)

            self.assertIsNone(
                TemplateDetector.detect_masked(uniform, template, mask)
            )
            self.assertIsNone(
                TemplateDetector.detect_masked(noise, template, mask)
            )

    def test_real_masked_anchors_survive_fill_changes_on_noisy_frames(self):
        anchor_dir = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "templates"
            / "anchors"
        )
        generator = np.random.default_rng(23)
        for filename, threshold in (
            ("enemy_anchor.png", 0.75),
            ("player_anchor.png", 0.90),
        ):
            anchor = self.load_image(anchor_dir / filename)
            dynamic = BarReader.create_mask(
                anchor,
                "red",
            ) | BarReader.create_mask(anchor, "blue")
            height, width = anchor.shape[:2]
            for fill in (15, 35, 70, 120):
                changed = anchor.copy()
                changed[dynamic] = (fill, fill, fill)
                source = generator.integers(
                    0,
                    256,
                    size=(640, 640, 3),
                    dtype=np.uint8,
                )
                source[123:123 + height, 271:271 + width] = changed

                match = TemplateDetector.detect_masked(
                    source,
                    self.template(anchor, threshold),
                    BarReader.create_structure_mask(anchor),
                )

                self.assertIsNotNone(match)
                self.assertEqual((match["x"], match["y"]), (271, 123))

    def test_enemy_anchor_rejects_the_player_hud_context(self):
        anchor_dir = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "templates"
            / "anchors"
        )
        enemy = self.load_image(anchor_dir / "enemy_anchor.png")
        player = self.load_image(anchor_dir / "player_anchor.png")
        source = np.zeros((640, 640, 3), dtype=np.uint8)
        player_height, player_width = player.shape[:2]
        source[
            100:100 + player_height,
            200:200 + player_width,
        ] = player
        template = self.template(enemy, 0.75)
        mask = BarReader.create_structure_mask(enemy)

        match = TemplateDetector.detect_masked(
            source,
            template,
            mask,
            grayscale=False,
        )

        self.assertIsNone(match)

    def test_coarse_search_refines_more_than_the_strongest_decoy(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "templates"
            / "anchors"
            / "enemy_anchor.png"
        )
        anchor = self.load_image(path)
        mask = BarReader.create_structure_mask(anchor)
        dynamic = BarReader.create_mask(anchor, "red")
        actual = anchor.copy()
        actual[dynamic] = (35, 35, 35)
        actual = cv2.GaussianBlur(actual, (3, 3), 0)

        decoy = anchor.astype(float)
        height, width = anchor.shape[:2]
        pattern = np.array([[1, -1], [-1, 1]])[:, :, None]
        for y in range(0, height - 1, 2):
            for x in range(0, width - 1, 2):
                block = decoy[y:y + 2, x:x + 2]
                mean = block.mean(axis=(0, 1))
                delta = np.minimum(mean, 255 - mean) * 0.95
                decoy[y:y + 2, x:x + 2] = mean + pattern * delta
        decoy = np.clip(np.rint(decoy), 0, 255).astype(np.uint8)

        source = np.random.default_rng(2).integers(
            0,
            256,
            size=(640, 640, 3),
            dtype=np.uint8,
        )
        source[123:123 + height, 271:271 + width] = actual
        source[400:400 + height, 100:100 + width] = decoy

        match = TemplateDetector.detect_masked(
            source,
            self.template(anchor, 0.75),
            mask,
        )

        self.assertEqual((match["x"], match["y"]), (271, 123))


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
