import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from core.models.player_state import PlayerState
from core.services.bar_reader import BarReader
from core.services.player_monitor import PlayerMonitor


class RecordingTemplates:

    def __init__(self):
        self.requests = []
        self.values = {
            "player_anchor": object(),
            "player_hud": object(),
            "player_hp": {"x": 1, "y": 2, "width": 4, "height": 3},
            "player_mp": {"x": 5, "y": 6, "width": 3, "height": 2},
        }

    def get(self, name):
        self.requests.append(name)
        return self.values.get(name)


class PlayerMonitorTests(unittest.TestCase):

    def test_configured_player_area_avoids_full_frame_search_on_miss(self):
        full_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        search_image = np.zeros((300, 540, 3), dtype=np.uint8)
        search_area = {"x": 600, "y": 740, "width": 540, "height": 300}
        detector = SimpleNamespace(detect=MagicMock(return_value=None))
        resolver = SimpleNamespace(crop=MagicMock(return_value=search_image))
        templates = SimpleNamespace(get=lambda name: search_area)
        monitor = PlayerMonitor(detector, resolver, SimpleNamespace(), templates)

        detection = monitor._detect_in_search_area(
            full_image,
            object(),
            "player_search_area",
        )

        self.assertIsNone(detection)
        detector.detect.assert_called_once_with(search_image, unittest.mock.ANY)

    def test_player_area_detection_restores_frame_coordinates(self):
        full_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        search_image = np.zeros((300, 540, 3), dtype=np.uint8)
        search_area = {"x": 600, "y": 740, "width": 540, "height": 300}
        detector = SimpleNamespace(
            detect=MagicMock(return_value={"x": 151, "y": 109})
        )
        resolver = SimpleNamespace(crop=MagicMock(return_value=search_image))
        templates = SimpleNamespace(get=lambda name: search_area)
        monitor = PlayerMonitor(detector, resolver, SimpleNamespace(), templates)

        detection = monitor._detect_in_search_area(
            full_image,
            object(),
            "player_search_area",
        )

        self.assertEqual(detection, {"x": 751, "y": 849})

    def test_update_reads_only_hp_and_mp_from_the_player_hud(self):
        image = np.zeros((12, 12, 3), dtype=np.uint8)
        anchor = object()
        hud = object()
        detector = SimpleNamespace(detect=MagicMock(return_value=anchor))
        resolver = SimpleNamespace(
            resolve=MagicMock(return_value=hud),
            crop=MagicMock(return_value=image),
        )
        bar_reader = SimpleNamespace(
            read_hp=MagicMock(return_value=76.5),
            read_mp=MagicMock(return_value=38.25),
        )
        templates = RecordingTemplates()
        monitor = PlayerMonitor(detector, resolver, bar_reader, templates)
        player = PlayerState()

        with patch(
            "core.services.player_monitor.time.perf_counter",
            return_value=12.5,
        ):
            updated = monitor.update(image, player)

        self.assertTrue(updated)
        self.assertEqual(player.hp_percent, 76.5)
        self.assertTrue(player.hp_valid)
        self.assertEqual(player.hp_updated_at, 12.5)
        self.assertEqual(player.mp_percent, 38.25)
        self.assertTrue(player.mp_valid)
        self.assertEqual(player.mp_updated_at, 12.5)
        self.assertEqual(
            templates.requests,
            ["player_anchor", "player_hud", "player_hp", "player_mp"],
        )
        detector.detect.assert_called_once_with(
            image,
            templates.values["player_anchor"],
        )
        resolver.resolve.assert_called_once_with(
            anchor,
            templates.values["player_hud"],
        )
        resolver.crop.assert_called_once_with(image, hud)

        hp_image = bar_reader.read_hp.call_args.args[0]
        mp_image = bar_reader.read_mp.call_args.args[0]
        self.assertEqual(hp_image.shape, (3, 4, 3))
        self.assertEqual(mp_image.shape, (2, 3, 3))

    def test_missing_player_hud_does_not_touch_resources(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)
        detector = SimpleNamespace(detect=MagicMock(return_value=None))
        resolver = SimpleNamespace(
            resolve=MagicMock(),
            crop=MagicMock(),
        )
        bar_reader = SimpleNamespace(
            read_hp=MagicMock(),
            read_mp=MagicMock(),
        )
        templates = RecordingTemplates()
        monitor = PlayerMonitor(detector, resolver, bar_reader, templates)
        player = PlayerState()
        player.hp_percent = 60
        player.mp_percent = 40

        updated = monitor.update(image, player)

        self.assertFalse(updated)
        self.assertEqual(player.hp_percent, 60)
        self.assertEqual(player.mp_percent, 40)
        resolver.resolve.assert_not_called()
        resolver.crop.assert_not_called()
        bar_reader.read_hp.assert_not_called()
        bar_reader.read_mp.assert_not_called()

    def test_unreadable_resource_does_not_replace_the_last_valid_sample(self):
        image = np.zeros((12, 12, 3), dtype=np.uint8)
        detector = SimpleNamespace(detect=MagicMock(return_value=object()))
        resolver = SimpleNamespace(
            resolve=MagicMock(return_value=object()),
            crop=MagicMock(return_value=image),
        )
        bar_reader = SimpleNamespace(
            read_hp=MagicMock(side_effect=[35, None]),
            read_mp=MagicMock(side_effect=[80, 60]),
        )
        monitor = PlayerMonitor(
            detector,
            resolver,
            bar_reader,
            RecordingTemplates(),
        )
        player = PlayerState()

        with patch(
            "core.services.player_monitor.time.perf_counter",
            side_effect=[10.0, 10.25],
        ):
            monitor.update(image, player)
            monitor.update(image, player)

        self.assertEqual(player.hp_percent, 35)
        self.assertEqual(player.hp_updated_at, 10.0)
        self.assertTrue(player.hp_valid)
        self.assertEqual(player.mp_percent, 60)
        self.assertEqual(player.mp_updated_at, 10.25)
        self.assertEqual(detector.detect.call_count, 1)
        self.assertEqual(resolver.resolve.call_count, 1)

    def test_transient_unreadable_bars_do_not_repeat_full_anchor_search(self):
        image = np.zeros((12, 12, 3), dtype=np.uint8)
        detector = SimpleNamespace(detect=MagicMock(return_value=object()))
        resolver = SimpleNamespace(
            resolve=MagicMock(return_value=object()),
            crop=MagicMock(return_value=image),
        )
        bar_reader = SimpleNamespace(
            read_hp=MagicMock(side_effect=[50, None, None]),
            read_mp=MagicMock(side_effect=[60, None, None]),
        )
        monitor = PlayerMonitor(
            detector,
            resolver,
            bar_reader,
            RecordingTemplates(),
        )
        player = PlayerState()

        monitor.update(image, player)
        monitor.update(image, player)
        monitor.update(image, player)

        self.assertEqual(detector.detect.call_count, 1)
        self.assertEqual(player.hp_percent, 50)
        self.assertEqual(player.mp_percent, 60)

    def test_anchor_reacquisition_uses_the_cached_hud_position(self):
        template_image = np.full((20, 30, 3), 35, dtype=np.uint8)
        template_image[5:15, 7:25] = (10, 15, 210)
        template = SimpleNamespace(
            image=template_image,
            threshold=0.9,
            name="player_anchor",
            type="anchor",
        )
        full_detection = {"x": 100, "y": 50}
        local_detection = {"x": 24, "y": 24}
        detector = MagicMock(
            side_effect=[full_detection, local_detection]
        )
        monitor = PlayerMonitor(
            SimpleNamespace(detect=detector),
            SimpleNamespace(),
            BarReader(),
            RecordingTemplates(),
        )
        image = np.zeros((200, 300, 3), dtype=np.uint8)

        first = monitor._detect_anchor(image, template)
        second = monitor._detect_anchor(image, template)

        self.assertEqual((first["x"], first["y"]), (100, 50))
        self.assertEqual((second["x"], second["y"]), (100, 50))
        self.assertEqual(detector.call_args_list[1].args[0].shape[:2], (68, 78))

    def test_missing_global_anchor_search_has_a_completion_backoff(self):
        template_image = np.full((20, 30, 3), 35, dtype=np.uint8)
        template_image[5:15, 7:25] = (10, 15, 210)
        template = SimpleNamespace(
            image=template_image,
            threshold=0.9,
            name="player_anchor",
            type="anchor",
        )
        detect = MagicMock(return_value=None)
        monitor = PlayerMonitor(
            SimpleNamespace(detect=detect),
            SimpleNamespace(),
            BarReader(),
            RecordingTemplates(),
        )
        image = np.zeros((200, 300, 3), dtype=np.uint8)

        with patch(
            "core.services.player_monitor.time.perf_counter",
            side_effect=[1.0, 1.2, 1.3, 1.8, 2.0],
        ):
            self.assertIsNone(monitor._detect_anchor(image, template))
            self.assertIsNone(monitor._detect_anchor(image, template))
            self.assertIsNone(monitor._detect_anchor(image, template))

        self.assertEqual(detect.call_count, 2)

    def test_one_missing_resource_eventually_revalidates_the_anchor(self):
        image = np.zeros((12, 12, 3), dtype=np.uint8)
        detector = SimpleNamespace(detect=MagicMock(return_value=object()))
        resolver = SimpleNamespace(
            resolve=MagicMock(return_value=object()),
            crop=MagicMock(return_value=image),
        )
        bar_reader = SimpleNamespace(
            read_hp=MagicMock(return_value=55),
            read_mp=MagicMock(return_value=None),
        )
        monitor = PlayerMonitor(
            detector,
            resolver,
            bar_reader,
            RecordingTemplates(),
        )
        player = PlayerState()

        for _ in range(8):
            monitor.update(image, player)

        self.assertEqual(detector.detect.call_count, 2)
        self.assertEqual(resolver.resolve.call_count, 2)
        self.assertTrue(player.hp_valid)
        self.assertFalse(player.mp_valid)

        bar_reader.read_hp.return_value = None
        bar_reader.read_mp.return_value = 45
        monitor.hp_misses = 0
        monitor.mp_misses = 0
        for _ in range(8):
            monitor.update(image, player)

        self.assertEqual(detector.detect.call_count, 3)
        self.assertTrue(player.mp_valid)

    def test_both_missing_resources_keep_the_fast_retry_signal(self):
        image = np.zeros((12, 12, 3), dtype=np.uint8)
        detector = SimpleNamespace(detect=MagicMock(return_value=object()))
        resolver = SimpleNamespace(
            resolve=MagicMock(return_value=object()),
            crop=MagicMock(return_value=image),
        )
        monitor = PlayerMonitor(
            detector,
            resolver,
            SimpleNamespace(
                read_hp=MagicMock(return_value=None),
                read_mp=MagicMock(return_value=None),
            ),
            RecordingTemplates(),
        )
        player = PlayerState()

        results = [monitor.update(image, player) for _ in range(8)]

        self.assertEqual(results, [False] * 8)
        self.assertGreaterEqual(detector.detect.call_count, 2)
        self.assertFalse(player.hp_valid)
        self.assertFalse(player.mp_valid)

    def test_partial_resource_crop_is_rejected(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)

        crop = PlayerMonitor.crop_region(
            image,
            {"x": 3, "y": 0, "width": 2, "height": 2},
        )

        self.assertIsNone(crop)

    def test_public_api_has_no_identity_executor_or_ocr_dependencies(self):
        parameters = list(inspect.signature(PlayerMonitor).parameters)
        self.assertEqual(
            parameters,
            ["detector", "resolver", "bar_reader", "templates"],
        )

        monitor = PlayerMonitor(
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
        )
        for attribute in (
            "executor",
            "identity_future",
            "identity_generation",
            "name_matcher",
            "entity_cache",
            "entity_database",
        ):
            self.assertFalse(hasattr(monitor, attribute), attribute)
        for method in (
            "set_executor",
            "poll",
            "refresh_name",
            "read_identity",
            "_schedule_identity",
            "_read_identity_data",
        ):
            self.assertFalse(hasattr(monitor, method), method)


if __name__ == "__main__":
    unittest.main()
