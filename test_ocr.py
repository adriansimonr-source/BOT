import time


from core.services.capture_engine import CaptureEngine
from core.services.coordinate_reader import CoordinateReader

from core.services.template_detector import TemplateDetector
from core.services.template_manager import TemplateManager
from core.services.hud_resolver import HUDResolver

from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager





class CoordinateReaderQuickTest:


    def __init__(self):


        print("==============================")
        print(" QUICK COORD TEST ")
        print("==============================")


        self.config = ConfigManager()

        self.game_manager = GameProfileManager()



        active = self.config.get(
            "active_game"
        )


        if active:

            self.game_manager.set_active_game(
                active
            )



        window = self.game_manager.get_window()


        width,height = self.game_manager.get_resolution()



        self.capture = CaptureEngine(
            window,
            width,
            height
        )


        self.templates = TemplateManager()

        self.detector = TemplateDetector()

        self.hud = HUDResolver()


        self.reader = CoordinateReader()



        self.frames = 20


        self.ok = 0

        self.fail = 0


        self.coords = []







    def get_coordinate_crop(
        self,
        image
    ):


        anchor = self.templates.get(
            "minimap_anchor"
        )


        detection = self.detector.detect(
            image,
            anchor
        )


        if detection is None:

            return None



        hud = self.hud.resolve(
            detection,
            self.templates.get(
                "minimap_hud"
            )
        )



        coord = self.templates.get(
            "player_coordinates"
        )



        box = {

            "x":
            hud["x"] +
            coord["x"],


            "y":
            hud["y"] +
            coord["y"],


            "width":
            coord["width"],


            "height":
            coord["height"]

        }



        return self.hud.crop(
            image,
            box
        )









    def run(self):


        self.capture.start()


        time.sleep(1)



        start = time.time()



        try:


            for i in range(
                self.frames
            ):


                frame = self.capture.get_frame()



                crop = self.get_coordinate_crop(
                    frame.image
                )


                if crop is None:

                    self.fail += 1

                    print(
                        "[FAIL] crop"
                    )

                    continue



                result = self.reader.read(
                    crop
                )



                if result is None:

                    self.fail += 1


                else:

                    self.ok += 1

                    self.coords.append(
                        result
                    )


                print(
                    i,
                    result
                )



        finally:


            self.capture.stop()



        elapsed = time.time() - start



        print()
        print("==============================")
        print(" RESULTADO")
        print("==============================")


        print(
            "Frames:",
            self.frames
        )


        print(
            "OK:",
            self.ok
        )


        print(
            "Fallos:",
            self.fail
        )


        print(
            "Tiempo:",
            round(elapsed,2),
            "seg"
        )


        if self.coords:


            xs = [
                c["x"]
                for c in self.coords
            ]


            ys = [
                c["y"]
                for c in self.coords
            ]


            print()

            print(
                "ESTABILIDAD"
            )


            print(
                "X:",
                min(xs),
                "-",
                max(xs)
            )


            print(
                "Y:",
                min(ys),
                "-",
                max(ys)
            )


            print(
                "ULTIMO:",
                self.coords[-1]
            )


        print()

        print(
            "FIN TEST"
        )






if __name__ == "__main__":


    test = CoordinateReaderQuickTest()

    test.run()