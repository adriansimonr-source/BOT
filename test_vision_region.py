import time
import cv2


from core.services.capture_engine import CaptureEngine
from core.services.vision_engine import VisionEngine
from core.services.region_manager import RegionManager

from core.models.region import Region




TITLE = "Kathana - The Reign of Shadow"


WIDTH = 1920
HEIGHT = 1080





def section(text):

    print()
    print("=" * 45)
    print(text)
    print("=" * 45)





# ======================================
# CAPTURE
# ======================================


section(
    "START CAPTURE"
)



capture = CaptureEngine(

    TITLE,

    WIDTH,

    HEIGHT

)



capture.start()



print(
    "[OK] Capture iniciado"
)







# ======================================
# REGIONS
# ======================================


section(
    "CREATE REGIONS"
)



regions = RegionManager()



#
# Regiones de prueba
# Ajustaremos luego con editor visual
#

regions.add(

    Region(

        "center",

        700,

        400,

        500,

        300

    )

)



print(

    regions.info()

)







# ======================================
# VISION
# ======================================


vision = VisionEngine(

    regions

)



print(

    "[OK] VisionEngine iniciado"

)








frames = 0

start = time.time()



try:


    while True:



        frame = capture.get_frame()



        result = vision.process(

            frame

        )




        crop = vision.process_region(

            frame,

            "center"

        )




        frames += 1



        fps = frames / (

            time.time() - start

        )






        image = cv2.resize(

            frame.image,

            (960,540)

        )



        region_view = cv2.resize(

            crop,

            (500,300)

        )





        cv2.putText(

            image,

            f"FPS {fps:.1f}",

            (20,40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0,255,0),

            2

        )




        cv2.imshow(

            "FULL FRAME",

            image

        )



        cv2.imshow(

            "REGION TEST",

            region_view

        )







        if frames == 1:


            section(
                "FIRST FRAME"
            )


            print(

                frame.info()

            )


            print(

                result.info()

            )






        if cv2.waitKey(1) == 27:

            break







finally:


    capture.stop()

    cv2.destroyAllWindows()





section(
    "TEST FINISHED"
)



print(

    "FPS FINAL:",

    frames/(time.time()-start)

)