import cv2

from core.services.capture_engine import CaptureEngine
from core.services.template_creator import TemplateCreator



TITLE = "Kathana - The Reign of Shadow"

WIDTH = 1920
HEIGHT = 1080





def main():


    print("=" * 40)
    print(" TEMPLATE CREATOR TEST ")
    print("=" * 40)



    capture = CaptureEngine(

        TITLE,

        WIDTH,

        HEIGHT

    )



    capture.start()



    print("[OK] Capture iniciado")



    frame = capture.get_frame()



    if frame is None:

        raise Exception(
            "Frame vacío"
        )



    print(

        "[OK] Frame recibido:",

        type(frame)

    )





    #
    # Intentamos obtener imagen
    #

    if hasattr(frame, "image"):

        image = frame.image


    elif hasattr(frame, "data"):

        image = frame.data


    elif hasattr(frame, "buffer"):

        image = frame.buffer


    else:

        raise Exception(

            "No se encuentra imagen dentro del Frame"

        )





    print(

        "[OK] Imagen obtenida:",

        type(image)

    )



    cv2.imwrite(

        "template_debug_frame.png",

        image

    )


    print(

        "[OK] Debug guardado"

    )





    creator = TemplateCreator(

        image

    )



    print()
    print("CONTROLES")
    print("----------------")
    print("Arrastrar = seleccionar")
    print("S = guardar template")
    print("P = guardar captura")
    print("ESC = salir")
    print("----------------")



    creator.run()






if __name__ == "__main__":

    main()