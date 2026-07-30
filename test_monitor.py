import time
import cv2

from core.services.capture_engine import CaptureEngine



TITLE = "Kathana - The Reign of Shadow"

WIDTH = 1920
HEIGHT = 1080

PREVIEW = (960, 540)



def section(text):

    print()
    print("=" * 40)
    print(text)
    print("=" * 40)





# ==========================================
# CAPTURE ENGINE
# ==========================================


section(
    "CAPTURE PIPELINE TEST"
)


capture = CaptureEngine(

    TITLE,

    WIDTH,

    HEIGHT

)



capture.start()


print(
    "[OK] Window -> D3D -> WGC -> GPU Pipeline"
)





# ==========================================
# LOOP
# ==========================================


frames = 0

start = time.time()


first = True



try:


    while True:



        frame = capture.get_frame()



        if first:


            section(
                "FRAME VALIDATION"
            )


            print(

                frame.info()

            )


            print(

                "[OK] Texture -> CPU -> Frame"

            )


            first = False





        frames += 1



        fps = frames / (
            time.time() - start
        )






        image = cv2.resize(

            frame.image,

            PREVIEW

        )



        cv2.putText(

            image,

            f"FPS: {fps:.1f}",

            (20,40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0,255,0),

            2

        )



        cv2.imshow(

            "BOT VISION",

            image

        )




        if cv2.waitKey(1) == 27:

            break





finally:


    capture.stop()


    cv2.destroyAllWindows()





section(
    "RESULT"
)



print(
    "Frames:",
    frames
)


print(
    "FPS:",
    round(
        frames/(time.time()-start),
        2
    )
)


print(
    "[OK] PIPELINE COMPLETED"
)