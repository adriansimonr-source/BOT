import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.managers.config_manager import ConfigManager
from core.services.template_manager import TemplateManager
from core.runtime_paths import (
    DATA_DIRECTORY_ENV,
    configure_bundled_tesseract,
    data_path,
    initialize_runtime_environment,
    resource_path,
)


class RuntimePathTests(unittest.TestCase):
    def test_source_resources_do_not_depend_on_current_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                config = ConfigManager()
            finally:
                os.chdir(previous)

        self.assertEqual(config.get("active_game"), "kathana")
        self.assertTrue(resource_path("data", "templates.json").is_file())

    def test_templates_load_from_unicode_path(self):
        with tempfile.TemporaryDirectory() as directory:
            data_directory = Path(directory) / "áéí" / "data"
            anchor_directory = data_directory / "templates" / "anchors"
            anchor_directory.mkdir(parents=True)
            anchor = anchor_directory / "test.png"
            anchor.write_bytes(
                resource_path(
                    "data",
                    "templates",
                    "anchors",
                    "player_anchor.png",
                ).read_bytes()
            )
            config = data_directory / "templates.json"
            config.write_text(
                '{"anchors":{"test":{"file":"test.png"}},"regions":{}}',
                encoding="utf-8",
            )

            manager = TemplateManager(config)

        self.assertIsNotNone(manager.get("test").image)

    def test_frozen_defaults_are_seeded_once_without_overwriting_user_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            defaults = bundle / "defaults"
            user_data = root / "user-data"
            initial_files = {
                "config.json": '{"active_game": "kathana"}',
                "games.json": '{"games": []}',
                "entities/enemies.json": "{}",
                "entities/items.json": "{}",
            }
            for relative, contents in initial_files.items():
                path = defaults / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle), create=True),
                patch.dict(
                    os.environ,
                    {DATA_DIRECTORY_ENV: str(user_data)},
                    clear=False,
                ),
            ):
                initialize_runtime_environment()
                config_path = data_path("config.json")
                self.assertEqual(
                    config_path.read_text(encoding="utf-8"),
                    initial_files["config.json"],
                )
                config_path.write_text('{"user": true}', encoding="utf-8")
                initialize_runtime_environment()
                self.assertEqual(
                    config_path.read_text(encoding="utf-8"),
                    '{"user": true}',
                )

    def test_bundled_tesseract_configures_executable_and_tessdata(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            executable = bundle / "tesseract" / "tesseract.exe"
            tessdata = executable.parent / "tessdata"
            tessdata.mkdir(parents=True)
            executable.touch()
            native_executable = Path("C:/SHORT/TESSER/tesseract.exe")
            native_tessdata = Path("C:/SHORT/TESSER/tessdata")

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle), create=True),
                patch.dict(os.environ, {"PATH": "existing"}, clear=False),
                patch(
                    "core.runtime_paths._native_tool_path",
                    side_effect=[native_executable, native_tessdata],
                ),
            ):
                result = configure_bundled_tesseract()

                self.assertEqual(result, native_executable)
                self.assertEqual(
                    os.environ["TESSDATA_PREFIX"],
                    str(native_tessdata),
                )
                self.assertEqual(
                    os.environ["PATH"].split(os.pathsep)[0],
                    str(native_executable.parent),
                )


if __name__ == "__main__":
    unittest.main()
