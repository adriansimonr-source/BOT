import win32con
import win32gui
import win32api


KEY_MAP = {
    **{f"F{number}": 0x6F + number for number in range(1, 11)},
    **{str(number): 0x30 + number for number in range(1, 10)},
    "E": 0x45,
    "R": 0x52,
    "F": 0x46,
    "A": 0x41,
    "D": 0x44,
    "W": 0x57,
}


class WindowInputDriver:

    @staticmethod
    def _virtual_key(key):
        return KEY_MAP.get(str(key).upper())

    @staticmethod
    def _message_lparam(vk, released=False):
        scan_code = win32api.MapVirtualKey(vk, 0)
        value = 1 | (scan_code << 16)
        if released:
            value |= (1 << 30) | (1 << 31)
        return value

    def key_down(self, hwnd, key):
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False

        vk = self._virtual_key(key)
        if vk is None:
            return False

        try:
            win32gui.PostMessage(
                hwnd,
                win32con.WM_KEYDOWN,
                vk,
                self._message_lparam(vk),
            )
        except win32gui.error:
            return False

        return True

    def key_up(self, hwnd, key):
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False

        vk = self._virtual_key(key)
        if vk is None:
            return False

        try:
            win32gui.PostMessage(
                hwnd,
                win32con.WM_KEYUP,
                vk,
                self._message_lparam(vk, released=True),
            )
        except win32gui.error:
            return False

        return True
