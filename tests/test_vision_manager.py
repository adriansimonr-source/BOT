import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from core.managers.vision_manager import VisionManager
from core.models.player_state import PlayerState
from core.services.minimap_heading_detector import HeadingDetection


class VisionManagerTests(unittest.TestCase):

    @staticmethod
    def create_manager():
        manager = VisionManager.__new__(VisionManager)
        manager.running = True
        manager.latest_image = object()
        manager.minimap_interval = 1.0
        manager.coordinate_interval = 1.0
        manager.navigation_coordinate_interval = 0.5
        manager.last_minimap_update = 0.0
        manager.last_coordinate_update = 0.0
        manager.last_heading_update = 1.0
        manager.poll = MagicMock()
        manager.update_minimap = MagicMock()
        manager._update_coordinates = MagicMock()
        manager._update_heading = MagicMock()
        return manager

    def test_minimap_miss_in_configured_area_does_not_search_full_frame(self):
        manager = VisionManager.__new__(VisionManager)
        full_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        search_image = np.zeros((250, 350, 3), dtype=np.uint8)
        search_area = {"x": 1500, "y": 0, "width": 420, "height": 320}
        template = object()
        manager.templates = SimpleNamespace(get=lambda name: search_area)
        manager.resolver = SimpleNamespace(crop=MagicMock(return_value=search_image))
        manager.detector = SimpleNamespace(detect=MagicMock(return_value=None))

        detection = manager._detect_minimap_anchor(full_image, template)

        self.assertIsNone(detection)
        manager.detector.detect.assert_called_once_with(search_image, template)

    def test_minimap_detection_in_configured_area_restores_frame_coordinates(self):
        manager = VisionManager.__new__(VisionManager)
        full_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        search_image = np.zeros((250, 350, 3), dtype=np.uint8)
        search_area = {"x": 1500, "y": 20, "width": 420, "height": 320}
        template = object()
        manager.templates = SimpleNamespace(get=lambda name: search_area)
        manager.resolver = SimpleNamespace(crop=MagicMock(return_value=search_image))
        manager.detector = SimpleNamespace(
            detect=MagicMock(return_value={"x": 12, "y": 8})
        )

        detection = manager._detect_minimap_anchor(full_image, template)

        self.assertEqual(detection, {"x": 1512, "y": 28})
        manager.detector.detect.assert_called_once_with(search_image, template)

    def test_navigation_only_advances_coordinate_read_at_half_second(self):
        manager = self.create_manager()
        state = SimpleNamespace(navigation_active=True)

        with patch(
            "core.managers.vision_manager.time.perf_counter",
            return_value=0.5,
        ):
            manager.update_auxiliary(state)

        manager._update_coordinates.assert_called_once_with(
            manager.latest_image
        )
        manager.update_minimap.assert_not_called()
        self.assertEqual(manager.last_coordinate_update, 0.5)
        self.assertEqual(manager.last_minimap_update, 0.0)

    def test_coordinates_keep_one_second_interval_without_navigation(self):
        manager = self.create_manager()
        state = SimpleNamespace(navigation_active=False)

        with patch(
            "core.managers.vision_manager.time.perf_counter",
            return_value=0.5,
        ):
            manager.update_auxiliary(state)

        manager._update_coordinates.assert_not_called()
        manager.update_minimap.assert_not_called()
        self.assertEqual(manager.last_coordinate_update, 0.0)

    def test_regular_minimap_cycle_includes_due_coordinate_read(self):
        manager = self.create_manager()
        state = SimpleNamespace(navigation_active=True)

        with patch(
            "core.managers.vision_manager.time.perf_counter",
            return_value=1.0,
        ):
            manager.update_auxiliary(state)

        manager.update_minimap.assert_called_once_with(
            manager.latest_image,
            state,
            read_coordinates=True,
            read_heading=False,
        )
        manager._update_coordinates.assert_not_called()
        self.assertEqual(manager.last_coordinate_update, 1.0)
        self.assertEqual(manager.last_minimap_update, 1.0)

    def test_coordinate_history_uses_frame_time_instead_of_ocr_finish(self):
        manager = VisionManager.__new__(VisionManager)
        manager.coordinate_future = SimpleNamespace(
            done=lambda: True,
            result=lambda: {"x": 120, "y": 130},
        )
        manager.coordinate_submitted_at = 12.5
        state = SimpleNamespace(player=PlayerState())

        manager._poll_coordinate(state)

        self.assertEqual(state.player.position_updated_at, 12.5)
        self.assertEqual(
            state.player.position_history,
            [(1, 12.5, 120, 130)],
        )

    @patch("core.managers.vision_manager.CoordinateReader")
    def test_reset_discards_pending_ocr_and_isolates_its_reader(
        self,
        coordinate_reader_type,
    ):
        manager = VisionManager.__new__(VisionManager)
        old_reader = MagicMock()
        pending = MagicMock()
        replacement = MagicMock()
        coordinate_reader_type.return_value = replacement
        manager.debug_enabled = False
        manager.coordinate_reader = old_reader
        manager.coordinate_future = pending
        manager.coordinate_submitted_at = 12.5

        manager.reset_position_reader()

        pending.cancel.assert_called_once_with()
        self.assertIsNone(manager.coordinate_future)
        self.assertIsNone(manager.coordinate_submitted_at)
        self.assertIs(manager.coordinate_reader, replacement)
        coordinate_reader_type.assert_called_once_with(debug=False)

    def test_navigation_reads_heading_at_ten_hertz_without_anchor_search(self):
        manager = self.create_manager()
        manager.last_heading_update = 0.0
        manager.last_minimap_update = 0.1
        state = SimpleNamespace(navigation_active=True)

        with patch(
            "core.managers.vision_manager.time.perf_counter",
            return_value=0.1,
        ):
            manager.update_auxiliary(state)

        manager._update_heading.assert_called_once_with(
            manager.latest_image,
            state,
        )
        manager.update_minimap.assert_not_called()

    def test_filtered_heading_uses_the_frame_timestamp(self):
        manager = VisionManager.__new__(VisionManager)
        manager.latest_image_observed_at = 12.5
        manager.templates = SimpleNamespace(
            get=lambda name: {
                "x": 0,
                "y": 0,
                "width": 50,
                "height": 50,
            } if name == "player_direction" else None
        )
        manager.heading_detector = SimpleNamespace(
            update=lambda image, observed_at: HeadingDetection(
                90.0,
                0.8,
                observed_at,
            )
        )
        state = SimpleNamespace(player=PlayerState())

        manager._read_heading(np.zeros((50, 50, 3), dtype=np.uint8), state)

        self.assertEqual(state.player.minimap_heading_deg, 90.0)
        self.assertEqual(state.player.minimap_heading_updated_at, 12.5)

    def test_failed_player_hud_detection_is_retried_after_100_ms(self):
        manager = VisionManager.__new__(VisionManager)
        frame = SimpleNamespace(image=np.zeros((2, 2, 3), dtype=np.uint8))
        manager.running = True
        manager.capture = SimpleNamespace(get_frame=lambda: frame)
        manager.enemy_monitor = SimpleNamespace(update=MagicMock())
        manager.player_monitor = SimpleNamespace(
            update=MagicMock(return_value=False)
        )
        manager.last_player_update = 0.0
        state = SimpleNamespace(
            player=PlayerState(),
            target=SimpleNamespace(exists=False),
            in_combat=False,
        )

        with patch(
            "core.managers.vision_manager.time.perf_counter",
            side_effect=[1.0, 1.0, 1.2],
        ):
            manager.update(state)

        self.assertAlmostEqual(manager.last_player_update, 1.05)
        manager.player_monitor.update.assert_called_once()

    def test_stop_finishes_ocr_cleanup_even_if_capture_stop_fails(self):
        manager = VisionManager.__new__(VisionManager)
        manager.capture = SimpleNamespace(
            stop=MagicMock(side_effect=RuntimeError("capture stop failed")),
        )
        manager.running = True
        manager.latest_image = object()
        manager.latest_image_observed_at = 1.0
        manager.last_minimap_hud = object()
        manager.heading_detector = SimpleNamespace(reset=MagicMock())
        manager.coordinate_future = SimpleNamespace(cancel=MagicMock())
        manager.coordinate_submitted_at = 1.0
        manager.enemy_monitor = SimpleNamespace(set_executor=MagicMock())
        executor = SimpleNamespace(shutdown=MagicMock())
        manager.ocr_executor = executor

        with self.assertRaisesRegex(RuntimeError, "capture stop failed"):
            manager.stop()

        self.assertFalse(manager.running)
        self.assertIsNone(manager.coordinate_future)
        manager.enemy_monitor.set_executor.assert_called_once_with(None)
        executor.shutdown.assert_called_once_with(
            wait=True,
            cancel_futures=True,
        )
        self.assertIsNone(manager.ocr_executor)


if __name__ == "__main__":
    unittest.main()
