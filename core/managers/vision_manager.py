from core.services.capture_engine import CaptureEngine

from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.bar_reader import BarReader
from core.services.name_matcher import NameMatcher
from core.services.minimap_position_detector import MinimapPositionDetector

from core.services.player_monitor import PlayerMonitor
from core.services.enemy_monitor import EnemyMonitor


from core.managers.entity_cache_manager import EntityCacheManager
from core.managers.entity_database_manager import EntityDatabaseManager

from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager

from core.system.system_info import SystemInfo

import cv2
import os



class VisionManager:


    def __init__(self):

        self.config = ConfigManager()

        self.game_profiles = GameProfileManager()

        self.system = SystemInfo()


        print(
            "[Sistema]",
            self.system.get_info()
        )



        active_game = self.config.get(
            "active_game"
        )


        if active_game:

            self.game_profiles.set_active_game(
                active_game
            )



        game = self.game_profiles.get_active_game()


        if game is None:

            raise Exception(
                "No hay juego activo configurado"
            )



        window_title = self.game_profiles.get_window()


        width, height = (
            self.game_profiles.get_resolution()
        )


        print(
            "[Vision]",
            "Juego:",
            game.get("name")
        )

        print(
            "[Vision]",
            "Ventana:",
            window_title
        )

        print(
            "[Vision]",
            "Resolución:",
            width,
            "x",
            height
        )



        self.capture = CaptureEngine(
            window_title,
            width,
            height
        )



        self.templates = TemplateManager()

        self.detector = TemplateDetector()

        self.resolver = HUDResolver()

        self.bar_reader = BarReader()

        self.name_matcher = NameMatcher()

        self.minimap_detector = MinimapPositionDetector()



        self.entity_database = EntityDatabaseManager()

        self.entity_cache = EntityCacheManager()



        self.name_matcher.load_enemy_templates(
            "data/entities/enemies"
        )


        self.name_matcher.load_player_templates(
            "data/entities/players"
        )



        self.player_monitor = PlayerMonitor(
            self.detector,
            self.resolver,
            self.bar_reader,
            self.templates,
            self.name_matcher,
            self.entity_cache,
            self.entity_database
        )



        self.enemy_monitor = EnemyMonitor(
            self.detector,
            self.resolver,
            self.bar_reader,
            self.templates,
            self.name_matcher,
            self.entity_cache,
            self.entity_database
        )



        self.running = False

        self.debug_minimap_saved = False





    def start(self):

        if self.running:

            return


        self.capture.start()


        self.running = True


        print(
            "[VisionManager] iniciado"
        )





    def update(
        self,
        state
    ):


        if not self.running:

            return



        frame = self.capture.get_frame()


        if frame is None:

            return



        image = frame.image



        self.player_monitor.update(
            image,
            state.player
        )



        self.update_minimap(
            image,
            state
        )



        self.enemy_monitor.update(
            image,
            state.target
        )





    def update_minimap(
        self,
        image,
        state
    ):


        minimap_template = self.templates.get(
            "minimap"
        )


        if minimap_template is None:

            print(
                "[Minimap] template no encontrado"
            )

            return



        detection = self.detector.detect(
            image,
            minimap_template
        )


        if detection is None:

            print(
                "[Minimap] anchor no detectado"
            )

            return



        minimap_region = self.templates.get(
            "minimap_area"
        )


        if minimap_region is None:

            print(
                "[Minimap] region no encontrada"
            )

            return



        minimap_hud = self.resolver.resolve(
            detection,
            minimap_region
        )


        print(
            "[MINIMAP HUD]",
            minimap_hud
        )



        if minimap_hud is None:

            return



        crop = self.resolver.crop(
            image,
            minimap_hud
        )



        self.save_debug_minimap(
            crop
        )



        position = self.minimap_detector.detect(
            image,
            minimap_hud
        )


        if position is None:

            print(
                "[Minimap] jugador no detectado"
            )

            return



        state.player.minimap_position = position


        print(
            "[Minimap]",
            position
        )





    def save_debug_minimap(
        self,
        image
    ):


        if self.debug_minimap_saved:

            return


        os.makedirs(
            "debug",
            exist_ok=True
        )


        cv2.imwrite(
            "debug/minimap.png",
            image
        )


        self.debug_minimap_saved = True


        print(
            "[Minimap] debug guardado"
        )





    def stop(self):

        self.capture.stop()

        self.running = False


        print(
            "[VisionManager] detenido"
        )