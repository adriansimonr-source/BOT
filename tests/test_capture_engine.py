import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from core.services.capture_engine import CaptureEngine


class FakeReader:

    def __init__(self):
        self.released = []

    def try_get_next_frame(self):
        return "frame"

    def release_frame(self, frame):
        self.released.append(frame)


class FakeFrameManager:

    def __init__(self):
        self.released = []

    def set_frame(self, _frame):
        pass

    def get_surface(self):
        return "surface"

    def release_surface(self, surface):
        self.released.append(surface)


class FakeSurfaceManager:

    def __init__(self):
        self.released = []

    def get_dxgi_access(self, _surface):
        return "access"

    def get_texture(self, _access):
        return "texture"

    def release_interface(self, interface):
        self.released.append(interface)


class FakeMap:

    def __init__(self):
        self.unmapped = []

    def map_texture(self, _texture):
        return "mapped"

    def unmap_texture(self, texture):
        self.unmapped.append(texture)


class CaptureEngineTests(unittest.TestCase):

    @staticmethod
    def create_engine(cpu):
        engine = CaptureEngine("Window", 100, 100)
        engine.running = True
        engine.reader = FakeReader()
        engine.frame_manager = FakeFrameManager()
        engine.surface_manager = FakeSurfaceManager()
        engine.staging_texture = "staging"
        engine.copy = SimpleNamespace(copy_resource=lambda *_args: True)
        engine.map = FakeMap()
        engine.cpu = cpu
        return engine

    def test_frame_interfaces_are_released_after_success(self):
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        cpu = SimpleNamespace(read_frame=lambda _mapped: image)
        engine = self.create_engine(cpu)

        frame = engine.get_frame()

        self.assertIs(frame.image, image)
        self.assertEqual(engine.map.unmapped, ["staging"])
        self.assertEqual(engine.surface_manager.released, ["texture", "access"])
        self.assertEqual(engine.frame_manager.released, ["surface"])
        self.assertEqual(engine.reader.released, ["frame"])

    def test_mapped_texture_and_interfaces_are_released_after_failure(self):
        def fail(_mapped):
            raise ValueError("conversion failed")

        engine = self.create_engine(SimpleNamespace(read_frame=fail))

        with self.assertRaises(ValueError):
            engine.get_frame()

        self.assertEqual(engine.map.unmapped, ["staging"])
        self.assertEqual(engine.surface_manager.released, ["texture", "access"])
        self.assertEqual(engine.frame_manager.released, ["surface"])
        self.assertEqual(engine.reader.released, ["frame"])

    def test_missing_frame_returns_after_the_short_timeout(self):
        engine = CaptureEngine("Window", 100, 100)
        engine.running = True
        engine.reader = SimpleNamespace(try_get_next_frame=lambda: None)

        with (
            patch(
                "core.services.capture_engine.time.perf_counter",
                side_effect=(0.0, 0.0, 0.011),
            ),
            patch("core.services.capture_engine.time.sleep") as sleep,
        ):
            self.assertIsNone(engine.get_frame())

        sleep.assert_called_once_with(0.005)


if __name__ == "__main__":
    unittest.main()
