import ctypes
import time


user32 = ctypes.windll.user32


KEYEVENTF_KEYUP = 0x0002



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





class KeyboardDriver:


    def press(
        self,
        key
    ):


        key = key.upper()



        if key not in KEY_MAP:

            print(
                f"[KEYBOARD] Tecla no soportada: {key}"
            )

            return



        vk = KEY_MAP[key]



        user32.keybd_event(
            vk,
            0,
            0,
            0
        )


        time.sleep(
            0.05
        )


        user32.keybd_event(
            vk,
            0,
            KEYEVENTF_KEYUP,
            0
        )


        print(
            f"[KEYBOARD] Press {key}"
        )