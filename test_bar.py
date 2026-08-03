import cv2
import os


from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector
from core.services.hud_resolver import HUDResolver
from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager



os.makedirs(
    "templates/coordinates/x",
    exist_ok=True
)


os.makedirs(
    "templates/coordinates/y",
    exist_ok=True
)



# ==============================
# MISMA CONFIG QUE VISIONMANAGER
# ==============================


config = ConfigManager()

profiles = GameProfileManager()


game = profiles.get_active_game()


if game is None:

    raise Exception(
        "No hay juego activo"
    )


window_title = profiles.get_window()


width, height = profiles.get_resolution()



print(
    "[TEST]",
    game.get("name")
)


print(
    "[WINDOW]",
    window_title
)


print(
    "[RESOLUTION]",
    width,
    height
)



capture = CaptureEngine(
    window_title,
    width,
    height
)



templates = TemplateManager()

detector = TemplateDetector()

resolver = HUDResolver()



capture.start()



print()
print("==============================")
print(" TEMPLATE COORDINATES")
print("==============================")
print()
print("ENTER = guardar")
print("ESC = salir")
print()



# mismos templates que VisionManager

minimap_template = templates.get(
    "minimap"
)


minimap_region = templates.get(
    "minimap_area"
)



if minimap_template is None:

    raise Exception(
        "Template minimap no encontrado"
    )


if minimap_region is None:

    raise Exception(
        "Region minimap_area no encontrada"
    )





while True:


    frame = capture.get_frame()


    if frame is None:

        continue



    image = frame.image



    detection = detector.detect(
        image,
        minimap_template
    )



    if detection is None:

        print(
            "[FAIL] minimap"
        )

        continue



    print(
        "[ANCHOR]",
        detection
    )



    hud = resolver.resolve(
        detection,
        minimap_region
    )


    print(
        "[HUD]",
        hud
    )



    crop = resolver.crop(
        image,
        hud
    )


    # este es el mismo crop que usas para coordenadas

    coordinate_box = crop[
        177:195,
        5:90
    ]



    cv2.imshow(
        "coordinate_box",
        coordinate_box
    )



    key = cv2.waitKey(1)



    if key == 13:


        x = input(
            "X actual: "
        )


        y = input(
            "Y actual: "
        )



        x_crop = coordinate_box[
            0:18,
            0:40
        ]


        y_crop = coordinate_box[
            0:18,
            45:80
        ]



        cv2.imwrite(
            f"templates/coordinates/x/{x}.png",
            x_crop
        )


        cv2.imwrite(
            f"templates/coordinates/y/{y}.png",
            y_crop
        )



        print(
            "[GUARDADO]",
            x,
            y
        )



    elif key == 27:

        break



capture.stop()

cv2.destroyAllWindows()