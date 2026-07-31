import cv2

from core.services.ocr_reader import OCRReader



BASE_PATH = "data/templates/regions"



def load_image(filename):

    path = f"{BASE_PATH}/{filename}"

    image = cv2.imread(path)

    if image is None:

        raise Exception(
            f"No se pudo cargar {path}"
        )

    return image





def crop(image, x, y, width, height):

    return image[
        y:y+height,
        x:x+width
    ]





def main():


    reader = OCRReader()



    print("\n========== PLAYER HUD ==========")


    hud = load_image(
        "player_hud.png"
    )


    # Según tu JSON actual
    # player_name:
    # x=5 y=0 width=200 height=18

    name_img = crop(
        hud,
        5,
        0,
        200,
        18
    )


    level_img = crop(
        hud,
        220,
        0,
        35,
        18
    )



    name = reader.read_text(
        name_img
    )


    level = reader.read_number(
        level_img
    )



    print(
        "Nombre:",
        name
    )


    print(
        "Nivel:",
        level
    )





    print("\n========== ENEMY HUD ==========")


    enemy = load_image(
        "enemy_hud.png"
    )


    # enemy_name:
    # x=0 y=0 width=200 height=18

    enemy_name_img = crop(
        enemy,
        0,
        0,
        200,
        18
    )


    enemy_level_img = crop(
        enemy,
        225,
        0,
        35,
        18
    )



    enemy_name = reader.read_text(
        enemy_name_img
    )


    enemy_level = reader.read_number(
        enemy_level_img
    )



    print(
        "Enemigo:",
        enemy_name
    )


    print(
        "Nivel enemigo:",
        enemy_level
    )





if __name__ == "__main__":

    main()