import sys
import os
import time
import cv2



# =====================================
# ROOT PROJECT
# =====================================

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    ROOT
)



from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.coordinate_reader import CoordinateReader


from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager





def main():


    print("==============================")
    print(" TEST COORDINATE PIPELINE")
    print("==============================")



    os.makedirs(
        "debug_coordinates",
        exist_ok=True
    )



    # =====================================
    # CONFIG IGUAL QUE VISION MANAGER
    # =====================================


    config = ConfigManager()

    profiles = GameProfileManager()



    active_game = config.get(
        "active_game"
    )



    if active_game:

        profiles.set_active_game(
            active_game
        )



    game = profiles.get_active_game()



    if game is None:

        raise Exception(
            "No hay juego activo configurado"
        )



    window = profiles.get_window()


    width, height = profiles.get_resolution()



    print(
        "[GAME]",
        game.get("name")
    )


    print(
        "[WINDOW]",
        window
    )


    print(
        "[RESOLUTION]",
        width,
        height
    )



    # =====================================
    # SERVICIOS
    # =====================================


    capture = CaptureEngine(

        window,

        width,

        height

    )


    templates = TemplateManager()


    detector = TemplateDetector()


    resolver = HUDResolver()


    reader = CoordinateReader()



    # =====================================
    # TEMPLATES
    # =====================================


    minimap_anchor = templates.get(
        "minimap_anchor"
    )


    minimap_hud_region = templates.get(
        "minimap_hud"
    )


    coordinate_region = templates.get(
        "player_coordinates"
    )



    if minimap_anchor is None:

        raise Exception(
            "Falta minimap_anchor"
        )


    if minimap_hud_region is None:

        raise Exception(
            "Falta minimap_hud"
        )


    if coordinate_region is None:

        raise Exception(
            "Falta player_coordinates"
        )



    print(
        "[OK] Configuración cargada"
    )



    # =====================================
    # CAPTURE
    # =====================================


    capture.start()


    time.sleep(1)



    # ==============================
    # PRUEBA 100 FRAMES
    # ==============================

    frames = 100



    ok = 0

    fail = 0


    values = []



    debug_saved = False




    try:


        for i in range(frames):


            frame = capture.get_frame()



            if frame is None:


                fail += 1

                continue



            image = frame.image



            # =================================
            # BUSCAR MINIMAP
            # =================================


            detection = detector.detect(

                image,

                minimap_anchor

            )



            if detection is None:


                print(
                    "[",
                    i,
                    "] minimap no encontrado"
                )


                fail += 1

                continue




            # =================================
            # RESOLVER HUD
            # =================================


            minimap_hud = resolver.resolve(

                detection,

                minimap_hud_region

            )



            if minimap_hud is None:


                fail += 1

                continue




            minimap_image = resolver.crop(

                image,

                minimap_hud

            )



            # =================================
            # COORDENADAS
            # =================================


            coordinate_box = minimap_image[

                coordinate_region["y"]:
                coordinate_region["y"] +
                coordinate_region["height"],


                coordinate_region["x"]:
                coordinate_region["x"] +
                coordinate_region["width"]

            ]



            if not debug_saved:


                cv2.imwrite(

                    "debug_coordinates/pipeline_coordinate_box.png",

                    coordinate_box

                )


                debug_saved = True





            result = reader.read(

                coordinate_box

            )



            print(

                i,

                result

            )



            if result:


                ok += 1


                values.append(

                    result

                )


            else:


                fail += 1





    finally:


        capture.stop()



    print()

    print("==============================")

    print(" RESULTADO")

    print("==============================")



    print(

        "Frames:",

        frames

    )


    print(

        "OK:",

        ok

    )


    print(

        "Fallos:",

        fail

    )



    if values:


        xs = [

            v["x"]

            for v in values

        ]


        ys = [

            v["y"]

            for v in values

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

            values[-1]

        )



    print()

    print(

        "Imagen guardada:",

        "debug_coordinates/pipeline_coordinate_box.png"

    )


    print()

    print(

        "FIN TEST"

    )





if __name__ == "__main__":

    main()