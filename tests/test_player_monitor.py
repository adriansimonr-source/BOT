import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from core.models.player_state import PlayerState
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
