import win32gui
import win32process


class WindowManager:


    def __init__(self):

        self.hwnd = None



    # =====================================
    # Buscar ventana por PID
    # =====================================

    def find_window_by_pid(
        self,
        pid
    ):

        result = []


        def callback(hwnd, _):

            if not win32gui.IsWindowVisible(hwnd):
                return


            _, window_pid = (
                win32process.GetWindowThreadProcessId(
                    hwnd
                )
            )


            if window_pid == pid:

                result.append(
                    hwnd
                )


        win32gui.EnumWindows(
            callback,
            None
        )


        if result:

            self.hwnd = result[0]

            return True


        return False



    # =====================================
    # Información ventana
    # =====================================

    def get_rect(self):

        if self.hwnd is None:

            return None


        return win32gui.GetWindowRect(
            self.hwnd
        )



    def get_position(self):

        rect = self.get_rect()


        if rect is None:

            return None


        left, top, right, bottom = rect


        return {
            "x": left,
            "y": top,
            "width": right-left,
            "height": bottom-top
        }