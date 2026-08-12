import os
import time
from concurrent.futures import ThreadPoolExecutor

import cv2

from core.managers.config_manager import ConfigManager
from core.managers.entity_cache_manager import EntityCacheManager
from core.managers.entity_database_manager import EntityDatabaseManager
from core.managers.game_profile_manager import GameProfileManager
from core.services.bar_reader import BarReader
from core.services.capture_engine import CaptureEngine
from core.services.coordinate_reader import CoordinateReader
from core.services.enemy_monitor import EnemyMonitor
from core.services.hud_resolver import HUDResolver
from core.services.name_matcher import NameMatcher
from core.services.player_monitor import PlayerMonitor
from core.services.template_detector import TemplateDetector
from core.services.template_manager import TemplateManager


class VisionManager:

    PLAYER_UPDATE_INTERVAL_SECONDS = 0.25
    MINIMAP_UPDATE_INTERVAL_SECONDS = 1.0
    COORDINATE_UPDATE_INTERVAL_SECONDS = 1.0
    NAVIGATION_COORDINATE_UPDATE_INTERVAL_SECONDS = 0.5

    def __init__(self, game_id=None, hwnd=None, capture_size=None):
        self.config = ConfigManager()
        self.game_profiles = GameProfileManager()

        active_game = game_id or self.config.get("active_game")
        if active_game:
            self.game_profiles.set_active_game(active_game)
        game = self.game_profiles.get_active_game()
        if game is None:
            raise Exception("No hay juego activo configurado")

        window_title = self.game_profiles.get_window()
        width, height = self.game_profiles.get_resolution()
        if capture_size:
            width, height = capture_size
        self.capture = CaptureEngine(window_title, width, height, hwnd=hwnd)
        self.templates = TemplateManager()
        self.detector = TemplateDetector()
        self.resolver = HUDResolver()
        self.bar_reader = BarReader()
        self.name_matcher = NameMatcher()
        self.debug_enabled = bool(
            self.config.get("features", "debug_mode")
        )
        self.coordinate_reader = CoordinateReader(debug=self.debug_enabled)
        self.entity_database = EntityDatabaseManager()
        self.entity_cache = EntityCacheManager()

        self.player_monitor = PlayerMonitor(
            self.detector,
            self.resolver,
            self.bar_reader,
            self.templates,
        )
        self.enemy_monitor = EnemyMonitor(
            self.detector,
            self.resolver,
            self.bar_reader,
            self.templates,
            self.name_matcher,
            self.entity_cache,
            self.entity_database,
        )

        self.running = False
        self.debug_minimap_saved = False
        self.minimap_interval = self.MINIMAP_UPDATE_INTERVAL_SECONDS
        self.coordinate_interval = self.COORDINATE_UPDATE_INTERVAL_SECONDS
        self.navigation_coordinate_interval = (
            self.NAVIGATION_COORDINATE_UPDATE_INTERVAL_SECONDS
        )
        self.last_minimap_update = 0.0
        self.last_coordinate_update = 0.0
        self.last_minimap_hud = None
        self.last_player_update = 0.0
        self.latest_image = None
        self.ocr_executor = None
        self.coordinate_future = None

    def start(self):
        if self.running:
            return
        self.coordinate_reader.reset()
        self.last_minimap_update = 0.0
        self.last_coordinate_update = 0.0
        self.last_minimap_hud = None
        self.last_player_update = 0.0
        self.latest_image = None
        self.debug_minimap_saved = False
        self.ocr_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="bot-ocr",
        )
        self.enemy_monitor.set_executor(self.ocr_executor)
        try:
            self.capture.start()
        except Exception:
            self.enemy_monitor.set_executor(None)
            self.ocr_executor.shutdown(wait=False, cancel_futures=True)
            self.ocr_executor = None
            raise
        self.running = True

    def reset_position_reader(self):
        self.coordinate_reader.reset()

    def poll(self, state):
        self.enemy_monitor.poll(state.target)
        self._poll_coordinate(state)

    def update(self, state):
        if not self.running:
            return
        frame = self.capture.get_frame()
        if frame is None:
            return

        image = frame.image
        self.latest_image = image
        self.enemy_monitor.update(image, state.target)
        now = time.perf_counter()
        if now - self.last_player_update >= self.PLAYER_UPDATE_INTERVAL_SECONDS:
            self.player_monitor.update(image, state.player)
            self.last_player_update = now
        state.in_combat = state.target.exists

    def update_auxiliary(self, state):
        self.poll(state)
        if not self.running or self.latest_image is None:
            return
        now = time.perf_counter()
        minimap_due = (
            now - self.last_minimap_update >= self.minimap_interval
        )
        coordinate_interval = (
            self.navigation_coordinate_interval
            if getattr(state, "navigation_active", False)
            else self.coordinate_interval
        )
        coordinate_due = (
            now - self.last_coordinate_update >= coordinate_interval
        )
        if not minimap_due and not coordinate_due:
            return

        if minimap_due:
            self.update_minimap(
                self.latest_image,
                state,
                read_coordinates=coordinate_due,
            )
            self.last_minimap_update = now
        elif coordinate_due:
            self._update_coordinates(self.latest_image)

        if coordinate_due:
            self.last_coordinate_update = now

    def update_minimap(self, image, state, read_coordinates=True):
        self.last_minimap_hud = None
        minimap_template = self.templates.get("minimap_anchor")
        if minimap_template is None:
            return
        detection = self._detect_minimap_anchor(image, minimap_template)
        if detection is None:
            return

        minimap_region = self.templates.get("minimap_hud")
        if minimap_region is None:
            return
        minimap_hud = self.resolver.resolve(detection, minimap_region)
        if minimap_hud is None:
            return
        self.last_minimap_hud = minimap_hud
        crop = self.resolver.crop(image, minimap_hud)
        if crop is None:
            return

        if read_coordinates:
            self._submit_coordinate_read(crop)

        self.save_debug_minimap(crop)

    def _detect_minimap_anchor(self, image, template):
        search_area = self.templates.get("minimap_search_area")
        search_image = self.resolver.crop(image, search_area)
        if search_image is not None:
            detection = self.detector.detect(search_image, template)
            if detection is not None:
                detection["x"] += max(0, int(search_area["x"]))
                detection["y"] += max(0, int(search_area["y"]))
                return detection
        return self.detector.detect(image, template)

    def _update_coordinates(self, image):
        minimap_hud = self.last_minimap_hud
        if minimap_hud is None:
            return
        crop = self.resolver.crop(image, minimap_hud)
        if crop is not None:
            self._submit_coordinate_read(crop)

    def _submit_coordinate_read(self, crop):
        coordinate_region = self.templates.get("player_coordinates")
        if (
            coordinate_region is not None
            and self.coordinate_future is None
            and self.ocr_executor is not None
        ):
            x = coordinate_region["x"]
            y = coordinate_region["y"]
            width = coordinate_region["width"]
            height = coordinate_region["height"]
            coordinate_box = crop[y:y + height, x:x + width]
            if coordinate_box.size:
                self.coordinate_future = self.ocr_executor.submit(
                    self.coordinate_reader.read,
                    coordinate_box.copy(),
                )

    def _poll_coordinate(self, state):
        future = self.coordinate_future
        if future is None or not future.done():
            return
        self.coordinate_future = None
        try:
            position = future.result()
        except Exception:
            return
        if position:
            state.player.update_position(position["x"], position["y"])

    def save_debug_minimap(self, image):
        if not self.debug_enabled or self.debug_minimap_saved:
            return
        os.makedirs("debug", exist_ok=True)
        cv2.imwrite("debug/minimap.png", image)
        self.debug_minimap_saved = True

    def stop(self):
        self.capture.stop()
        self.running = False
        self.latest_image = None
        self.last_minimap_hud = None
        self.coordinate_future = None
        self.enemy_monitor.set_executor(None)
        if self.ocr_executor:
            self.ocr_executor.shutdown(wait=False, cancel_futures=True)
            self.ocr_executor = None
