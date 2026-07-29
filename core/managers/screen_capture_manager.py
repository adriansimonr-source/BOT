import mss
import mss.tools


class ScreenCaptureManager:


    def __init__(self):

        self.monitor = None



    def set_region(
        self,
        x,
        y,
        width,
        height
    ):

        self.monitor = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }



    def capture(self):

        if self.monitor is None:
            return None


        with mss.mss() as sct:

            image = sct.grab(
                self.monitor
            )


            return image