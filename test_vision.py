import time
import cv2


from core.services.capture_engine import CaptureEngine
from core.services.vision_engine import VisionEngine



capture = CaptureEngine(

    "Kathana - The Reign of Shadow",

    1920,

    1080

)



vision = VisionEngine()



capture.start()



frames = 0

start = time.time()



try:


    while True:


        frame = capture.get_frame()


        detection = vision.process(

            frame

        )



        frames += 1



        fps = frames / (
            time.time()-start
        )




        image = cv2.resize(

            frame.image,

            (960,540)

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




        cv2.putText(

            image,

            f"CHANGE {detection.score:.1f}",

            (20,80),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0,255,255),

            2

        )




        cv2.imshow(

            "VISION",

            image

        )




        if cv2.waitKey(1)==27:

            break





finally:


    capture.stop()

    cv2.destroyAllWindows()