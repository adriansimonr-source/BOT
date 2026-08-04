import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.managers.vision_manager import VisionManager


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
        manager.poll = MagicMock()
        manager.update_minimap = MagicMock()
        manager._update_coordinates = MagicMock()
        return manager

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
        )
        manager._update_coordinates.assert_not_called()
        self.assertEqual(manager.last_coordinate_update, 1.0)
        self.assertEqual(manager.last_minimap_update, 1.0)


if __name__ == "__main__":
    unittest.main()
