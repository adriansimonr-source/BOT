from core.services.capture_engine import CaptureEngine

from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.ocr_reader import OCRReader

import cv2
import time





def crop_region(

    image,

    region

):


    if image is None:

        return None


    if region is None:

        return None



    x = region.get(

        "x",

        0

    )


    y = region.get(

        "y",

        0

    )


    width = region.get(

        "width",

        0

    )


    height = region.get(

        "height",

        0

    )



    return image[

        y:y + height,

        x:x + width

    ]







def save_debug(

    name,

    image

):


    if image is None:

        return


    cv2.imwrite(

        name,

        image

    )


    print(

        "[SAVE]",

        name

    )








def main():


    templates = TemplateManager()


    detector = TemplateDetector()


    resolver = HUDResolver()


    ocr = OCRReader()





    capture = CaptureEngine(

        "Kathana - The Reign of Shadow",

        1920,

        1080

    )





    capture.start()



    print(

        "Esperando captura..."

    )



    time.sleep(2)





    frame = capture.get_frame()



    if frame is None:

        print(

            "No hay frame"

        )

        return





    image = frame.image





    # ==============================
    # PLAYER
    # ==============================


    print()

    print(

        "========== PLAYER =========="

    )



    player_anchor_template = templates.get(

        "player_anchor"

    )



    player_anchor = detector.detect(

        image,

        player_anchor_template

    )



    print(

        "ANCHOR:",

        player_anchor

    )





    if player_anchor:


        player_hud_template = templates.get(

            "player_hud"

        )


        player_hud = resolver.resolve(

            player_anchor,

            player_hud_template

        )


        print(

            "HUD:",

            player_hud

        )



        hud_image = resolver.crop(

            image,

            player_hud

        )



        save_debug(

            "live_player_hud.png",

            hud_image

        )





        name_region = templates.get(

            "player_name"

        )


        name_image = crop_region(

            hud_image,

            name_region

        )


        save_debug(

            "live_player_name.png",

            name_image

        )





        print(

            "PLAYER NAME:",

            ocr.read_text(

                name_image

            )

        )





        level_region = templates.get(

            "player_level"

        )


        level_image = crop_region(

            hud_image,

            level_region

        )



        save_debug(

            "live_player_level.png",

            level_image

        )



        print(

            "PLAYER LEVEL:",

            ocr.read_number(

                level_image

            )

        )







    # ==============================
    # ENEMY
    # ==============================


    print()

    print(

        "========== ENEMY =========="

    )



    enemy_anchor_template = templates.get(

        "enemy_anchor"

    )



    enemy_anchor = detector.detect(

        image,

        enemy_anchor_template

    )



    print(

        "ANCHOR:",

        enemy_anchor

    )





    if enemy_anchor:


        enemy_hud_template = templates.get(

            "enemy_hud"

        )


        enemy_hud = resolver.resolve(

            enemy_anchor,

            enemy_hud_template

        )


        print(

            "HUD:",

            enemy_hud

        )



        hud_image = resolver.crop(

            image,

            enemy_hud

        )



        save_debug(

            "live_enemy_hud.png",

            hud_image

        )





        name_region = templates.get(

            "enemy_name"

        )


        name_image = crop_region(

            hud_image,

            name_region

        )


        save_debug(

            "live_enemy_name.png",

            name_image

        )





        print(

            "ENEMY NAME:",

            ocr.read_text(

                name_image

            )

        )





        level_region = templates.get(

            "enemy_level"

        )


        level_image = crop_region(

            hud_image,

            level_region

        )


        save_debug(

            "live_enemy_level.png",

            level_image

        )



        print(

            "ENEMY LEVEL:",

            ocr.read_number(

                level_image

            )

        )






    capture.stop()





if __name__ == "__main__":

    main()