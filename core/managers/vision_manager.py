from core.services.capture_engine import CaptureEngine

from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.bar_reader import BarReader
from core.services.name_matcher import NameMatcher

from core.services.player_monitor import PlayerMonitor
from core.services.enemy_monitor import EnemyMonitor

from core.managers.entity_cache_manager import EntityCacheManager





class VisionManager:


    def __init__(self):


        self.capture = CaptureEngine(

            "Kathana - The Reign of Shadow",

            1920,

            1080

        )



        self.templates = TemplateManager()


        self.detector = TemplateDetector()


        self.resolver = HUDResolver()


        self.bar_reader = BarReader()



        self.name_matcher = NameMatcher()



        self.name_matcher.load_enemy_templates(

            "data/entities/enemies"

        )


        self.name_matcher.load_player_templates(

            "data/entities/players"

        )





        self.entity_cache = EntityCacheManager()






        self.player_monitor = PlayerMonitor(

            self.detector,

            self.resolver,

            self.bar_reader,

            self.templates,

            self.name_matcher,

            self.entity_cache

        )







        self.enemy_monitor = EnemyMonitor(

            self.detector,

            self.resolver,

            self.bar_reader,

            self.templates,

            self.name_matcher,

            self.entity_cache

        )





        self.running = False







    # =====================================
    # START
    # =====================================


    def start(self):


        if self.running:

            return



        self.capture.start()


        self.running = True



        print(

            "[VisionManager] iniciado"

        )









    # =====================================
    # UPDATE
    # =====================================


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







        self.enemy_monitor.update(

            image,

            state.target

        )









    # =====================================
    # STOP
    # =====================================


    def stop(self):


        self.capture.stop()


        self.running = False



        print(

            "[VisionManager] detenido"

        )