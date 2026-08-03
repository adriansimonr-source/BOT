import win32gui
import win32con
import time



KEY_MAP = {

    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,

    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,

    "E": 0x45,
    "R": 0x52,
    "F": 0x46,

}





class WindowInputDriver:


    def press(
        self,
        hwnd,
        key
    ):


        if hwnd is None:

            print(
                "[WINDOW INPUT] HWND vacío"
            )

            return False



        key = key.upper()



        if key not in KEY_MAP:

            print(
                f"[WINDOW INPUT] Tecla no soportada {key}"
            )

            return False



        vk = KEY_MAP[key]



        win32gui.PostMessage(
            hwnd,
            win32con.WM_KEYDOWN,
            vk,
            0
        )


        time.sleep(
            0.05
        )


        win32gui.PostMessage(
            hwnd,
            win32con.WM_KEYUP,
            vk,
            0
        )


        print(
            f"[WINDOW INPUT] {key} -> HWND {hwnd}"
        )


        return True