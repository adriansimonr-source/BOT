from core.services.name_matcher import NameMatcher
from core.services.ocr_reader import OCRReader

import cv2





def main():


    matcher = NameMatcher()



    matcher.load_enemy_templates(
        "data/entities/enemies"
    )


    matcher.load_player_templates(
        "data/entities/players"
    )



    print(
        "Enemies templates:",
        matcher.enemy_templates.keys()
    )


    print(
        "Players templates:",
        matcher.player_templates.keys()
    )





    # ==========================
    # PRUEBA CON IMAGENES LIVE
    # ==========================


    enemy = cv2.imread(
        "live_enemy_name.png"
    )


    player = cv2.imread(
        "live_player_name.png"
    )





    print()

    print(
        "========== PLAYER =========="
    )


    print(
        matcher.read_player_name(
            player
        )
    )





    print()

    print(
        "========== ENEMY =========="
    )


    print(
        matcher.read_enemy_name(
            enemy
        )
    )





if __name__ == "__main__":

    main()