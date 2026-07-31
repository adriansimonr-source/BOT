import cv2


from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.services.target_validator import TargetValidator



TITLE = "Kathana - The Reign of Shadow"





def main():


    print("=" * 60)
    print(" TARGET VALIDATOR TEST ")
    print("=" * 60)



    # =====================================
    # Captura
    # =====================================


    capture = CaptureEngine(

        TITLE,

        1920,

        1080

    )


    capture.start()



    frame = capture.get_frame()



    image = frame.image



    cv2.imwrite(

        "validator_frame.png",

        image

    )



    print("[OK] Frame capturado")





    # =====================================
    # Servicios
    # =====================================


    manager = TemplateManager()

    detector = TemplateDetector()

    resolver = HUDResolver()

    validator = TargetValidator()





    # =====================================
    # PLAYER
    # =====================================


    print("\n--- PLAYER ---")



    player_template = manager.get(

        "player_anchor"

    )



    player_detection = detector.detect(

        image,

        player_template

    )



    print(

        "PLAYER ANCHOR:",

        player_detection

    )





    if player_detection:


        player_region = manager.get(

            "player_hud"

        )



        player_hud = resolver.resolve(

            player_detection,

            player_region

        )



        print(

            "PLAYER HUD:",

            player_hud

        )



        player_crop = resolver.crop(

            image,

            player_hud

        )



        cv2.imwrite(

            "player_hud_validator.png",

            player_crop

        )


        print(

            "[OK] player_hud_validator.png creado"

        )







    # =====================================
    # ENEMY
    # =====================================


    print("\n--- ENEMY ---")



    enemy_template = manager.get(

        "enemy_anchor"

    )



    enemy_detection = detector.detect(

        image,

        enemy_template

    )



    print(

        "ENEMY ANCHOR:",

        enemy_detection

    )





    if enemy_detection:



        enemy_region = manager.get(

            "enemy_hud"

        )



        enemy_hud = resolver.resolve(

            enemy_detection,

            enemy_region

        )



        print(

            "ENEMY HUD:",

            enemy_hud

        )



        enemy_crop = resolver.crop(

            image,

            enemy_hud

        )



        cv2.imwrite(

            "enemy_hud_validator.png",

            enemy_crop

        )


        print(

            "[OK] enemy_hud_validator.png creado"

        )





        # -----------------------------
        # VALIDACION
        # -----------------------------


        valid_enemy = validator.validate_enemy(

            enemy_crop

        )



        print()

        print(

            "RESULTADO ENEMY:",

            valid_enemy

        )


        if valid_enemy:

            print(

                "[OK] Objetivo enemigo valido"

            )

        else:

            print(

                "[FAIL] No parece enemigo"

            )



    else:


        print(

            "[INFO] No se detectó enemy_anchor"

        )





    print("\nFIN TEST")






if __name__ == "__main__":

    main()