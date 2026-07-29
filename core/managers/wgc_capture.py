import comtypes
import comtypes.client


class WGCCapture:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd


    def initialize(self):

        print(
            "Inicializando Windows Graphics Capture"
        )

        print(
            "HWND:",
            self.hwnd
        )


        comtypes.CoInitialize()


        return True