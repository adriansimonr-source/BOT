import cv2


from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.target_validator import TargetValidator
from core.services.bar_reader import BarReader

from core.models.combat_state import CombatState




TITLE = "Kathana - The Reign of Shadow"





def crop_relative(image, region):

    if image is None:
        return None


    x = region.get("x", 0)
    y = region.get("y", 0)

    w = region.get("width", 0)
    h = region.get("height", 0)



    return image[
        y:y+h,
        x:x+w
    ]






def main():


    print("=" * 70)
    print(" COMBAT STATE TEST ")
    print("=" * 70)



    # ============================
    # CAPTURE
    # ============================


    capture = CaptureEngine(

        TITLE,

        1920,

        1080

    )


    capture.start()



    frame = capture.get_frame()



    if frame is None:

        print("[ERROR] No frame")

        return



    image = frame.image



    cv2.imwrite(

        "combat_frame.png",

        image

    )



    print("[OK] Frame")





    # ============================
    # SERVICES
    # ============================


    templates = TemplateManager()


    detector = TemplateDetector()


    resolver = HUDResolver()


    validator = TargetValidator()


    reader = BarReader()



    state = CombatState()






    # ============================
    # PLAYER
    # ============================


    print()

    print("========== PLAYER ==========")



    player_anchor = detector.detect(

        image,

        templates.get(

            "player_anchor"

        )

    )



    if player_anchor:


        print(

            "PLAYER FOUND"

        )



        hud = resolver.resolve(

            player_anchor,

            templates.get(

                "player_hud"

            )

        )



        hud_img = resolver.crop(

            image,

            hud

        )



        cv2.imwrite(

            "state_player_hud.png",

            hud_img

        )





        hp_img = crop_relative(

            hud_img,

            templates.get(

                "player_hp"

            )

        )



        mp_img = crop_relative(

            hud_img,

            templates.get(

                "player_mp"

            )

        )



        cv2.imwrite(

            "state_player_hp.png",

            hp_img

        )


        cv2.imwrite(

            "state_player_mp.png",

            mp_img

        )



        state.player_detected = True



        state.player_hp = reader.read_hp(

            hp_img

        )


        state.player_mp = reader.read_mp(

            mp_img

        )



    else:


        print(

            "PLAYER NOT FOUND"

        )







    # ============================
    # ENEMY
    # ============================


    print()

    print("========== ENEMY ==========")



    enemies = detector.detect_all(

        image,

        templates.get(

            "enemy_anchor"

        )

    )



    print(

        "CANDIDATES:",

        len(enemies)

    )



    for enemy in enemies:


        hud = resolver.resolve(

            enemy,

            templates.get(

                "enemy_hud"

            )

        )



        hud_img = resolver.crop(

            image,

            hud

        )



        valid = validator.validate_enemy(

            hud_img

        )



        print(

            "VALID:",

            valid

        )



        if not valid:

            continue




        hp_img = crop_relative(

            hud_img,

            templates.get(

                "enemy_hp"

            )

        )



        cv2.imwrite(

            "state_enemy_hud.png",

            hud_img

        )


        cv2.imwrite(

            "state_enemy_hp.png",

            hp_img

        )



        state.enemy_detected = True



        state.enemy_hp = reader.read_enemy_hp(

            hp_img

        )



        break







    # ============================
    # RESULT
    # ============================


    print()

    print("=" * 70)

    print(" COMBAT STATE ")

    print("=" * 70)



    print()

    print("PLAYER")

    print(

        "Detected:",

        state.player_detected

    )

    print(

        "HP:",

        state.player_hp,

        "%"

    )

    print(

        "MP:",

        state.player_mp,

        "%"

    )



    print()

    print("ENEMY")

    print(

        "Detected:",

        state.enemy_detected

    )

    print(

        "HP:",

        state.enemy_hp,

        "%"

    )



    print()

    print(

        state.to_dict()

    )


    print()

    print("=" * 70)

    print(" END ")

    print("=" * 70)






if __name__ == "__main__":

    main()