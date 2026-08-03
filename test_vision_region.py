import os
import cv2
import pytesseract


from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver

from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager


import numpy as np





class CoordinatesOCRTest:



    def __init__(self):


        print("\n=== INIT TEST ===")


        self.config = ConfigManager()

        self.games = GameProfileManager()



        active_game = self.config.get(
            "active_game"
        )


        if active_game:

            self.games.set_active_game(
                active_game
            )



        game = self.games.get_active_game()


        if game is None:

            raise Exception(
                "No hay juego activo"
            )



        window = self.games.get_window()


        width,height = (
            self.games.get_resolution()
        )



        print(
            "[GAME]",
            window,
            width,
            height
        )



        self.capture = CaptureEngine(
            window,
            width,
            height
        )



        self.templates = TemplateManager()


        self.detector = TemplateDetector()


        self.resolver = HUDResolver()



        print("\n=== TEMPLATES ===")

        for t in self.templates.list():

            print(
                t
            )




        self.capture.start()



        os.makedirs(
            "debug_coordinates",
            exist_ok=True
        )







    def run(self):


        frame = self.capture.get_frame()



        if frame is None:

            raise Exception(
                "No hay frame"
            )



        image = frame.image



        cv2.imwrite(
            "debug_coordinates/fullscreen.png",
            image
        )



        print(
            "\n=== DETECT MINIMAP ==="
        )



        minimap_template = self.templates.get(
            "minimap_anchor"
        )



        detection = self.detector.detect(
            image,
            minimap_template
        )



        if detection is None:

            raise Exception(
                "No detecta minimap_anchor"
            )



        print(
            "[ANCHOR]",
            detection
        )




        print(
            "\n=== RESOLVE HUD ==="
        )


        minimap_region = self.templates.get(
            "minimap_hud"
        )



        minimap_hud = self.resolver.resolve(
            detection,
            minimap_region
        )



        print(
            "[HUD]",
            minimap_hud
        )



        minimap = self.resolver.crop(
            image,
            minimap_hud
        )



        cv2.imwrite(
            "debug_coordinates/minimap.png",
            minimap
        )






        print(
            "\n=== RESOLVE COORDINATES ==="
        )



        coordinates_region = self.templates.get(
            "player_coordinates"
        )



        coordinates_box = self.resolve_child(
            minimap_hud,
            coordinates_region
        )



        print(
            "[COORD BOX]",
            coordinates_box
        )




        crop = self.crop(
            image,
            coordinates_box
        )



        cv2.imwrite(
            "debug_coordinates/coordinates_original.png",
            crop
        )




        result = self.read_coordinates(
            crop
        )



        print(
            "\nOCR RESULT:"
        )

        print(
            result
        )




        self.capture.stop()



        print(
            "\nFIN TEST"
        )









    def resolve_child(
        self,
        parent,
        region
    ):


        return {


            "x":
            parent["x"] + region["x"],


            "y":
            parent["y"] + region["y"],


            "width":
            region["width"],


            "height":
            region["height"]

        }








    def crop(
        self,
        image,
        box
    ):


        return image[

            box["y"]:
            box["y"]+box["height"],

            box["x"]:
            box["x"]+box["width"]

        ]









    def read_coordinates(
        self,
        image
    ):


        print(
            "[OCR] Procesando..."
        )


        cv2.imwrite(
            "debug_coordinates/ocr_input.png",
            image
        )



        # ampliar

        resized = cv2.resize(
            image,
            None,
            fx=8,
            fy=8,
            interpolation=cv2.INTER_CUBIC
        )


        cv2.imwrite(
            "debug_coordinates/ocr_resize.png",
            resized
        )




        hsv = cv2.cvtColor(
            resized,
            cv2.COLOR_BGR2HSV
        )



        # texto blanco

        mask = cv2.inRange(
            hsv,
            np.array(
                [0,0,120]
            ),
            np.array(
                [180,140,255]
            )
        )



        cv2.imwrite(
            "debug_coordinates/ocr_mask.png",
            mask
        )



        kernel = np.ones(
            (2,2),
            np.uint8
        )


        clean = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel
        )



        cv2.imwrite(
            "debug_coordinates/ocr_clean.png",
            clean
        )





        text = pytesseract.image_to_string(

            clean,

            config=
            "--psm 7 "
            "-c tessedit_char_whitelist=0123456789/"

        )



        return text.strip()












if __name__ == "__main__":


    test = CoordinatesOCRTest()


    try:

        test.run()


    except Exception as e:

        print(
            "\nERROR:",
            e
        )

        test.capture.stop()