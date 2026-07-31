import cv2


from core.services.capture_engine import CaptureEngine
from core.services.template_manager import TemplateManager
from core.services.template_detector import TemplateDetector



TITLE = "Kathana - The Reign of Shadow"

WIDTH = 1920
HEIGHT = 1080




def get_image(frame):

    if hasattr(frame, "image"):
        return frame.image

    if hasattr(frame, "data"):
        return frame.data

    return frame





def main():

    print()
    print("=" * 50)
    print(" ANCHOR DETECTOR TEST ")
    print("=" * 50)



    capture = CaptureEngine(

        TITLE,

        WIDTH,

        HEIGHT

    )


    capture.start()


    frame = capture.get_frame()


    image = get_image(frame)



    cv2.imwrite(

        "anchor_test_frame.png",

        image

    )



    print(

        "[OK] Frame guardado"

    )





    manager = TemplateManager()



    detector = TemplateDetector()



    output = image.copy()



    for name in [

        "player_anchor",

        "enemy_anchor"

    ]:


        template = manager.get(name)



        if template is None:


            print(

                "[ERROR] No existe:",

                name

            )

            continue





        print()

        print(

            "Buscando:",

            name

        )



        result = detector.detect(

            image,

            template

        )



        print(result)



        detector.draw_detection(

            output,

            result

        )





    cv2.imwrite(

        "anchor_detection.png",

        output

    )


    print()

    print(

        "[OK] anchor_detection.png creado"

    )





if __name__ == "__main__":

    main()