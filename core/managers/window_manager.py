import win32gui
import win32process


class WindowManager:


    def __init__(self):

        self.hwnd = None



    # =====================================
    # Buscar ventana por PID + título
    # =====================================

    def find_window_by_pid(
        self,
        pid,
        window_title=None
    ):

        windows = []


        def callback(hwnd, _):

            if not win32gui.IsWindowVisible(hwnd):

                return


            _, window_pid = (
                win32process.GetWindowThreadProcessId(
                    hwnd
                )
            )


            if window_pid != pid:

                return


            title = win32gui.GetWindowText(
                hwnd
            )


            rect = win32gui.GetWindowRect(
                hwnd
            )


            width = rect[2] - rect[0]

            height = rect[3] - rect[1]


            windows.append(
                {
                    "hwnd": hwnd,
                    "title": title,
                    "rect": rect,
                    "width": width,
                    "height": height
                }
            )



        win32gui.EnumWindows(
            callback,
            None
        )


        print(
            "VENTANAS POR PID:"
        )


        for window in windows:

            print(window)



        for window in windows:


            if window_title:

                if (
                    window_title.lower()
                    not in
                    window["title"].lower()
                ):

                    continue



            if window["width"] < 500:

                continue


            if window["height"] < 300:

                continue



            self.hwnd = (
                window["hwnd"]
            )


            print(
                "VENTANA SELECCIONADA POR PID:"
            )

            print(
                window
            )


            return True



        return False




    # =====================================
    # Buscar ventana por título global
    # =====================================

    def find_window_by_title(
        self,
        title
    ):

        windows = []


        def callback(hwnd, _):

            if not win32gui.IsWindowVisible(hwnd):

                return


            window_title = (
                win32gui.GetWindowText(hwnd)
            )


            if (
                title.lower()
                in
                window_title.lower()
            ):


                rect = (
                    win32gui.GetWindowRect(hwnd)
                )


                width = (
                    rect[2] - rect[0]
                )

                height = (
                    rect[3] - rect[1]
                )


                windows.append(
                    {
                        "hwnd": hwnd,
                        "title": window_title,
                        "rect": rect,
                        "width": width,
                        "height": height
                    }
                )



        win32gui.EnumWindows(
            callback,
            None
        )



        print(
            "VENTANAS POR TITULO:"
        )


        for window in windows:

            print(window)



        for window in windows:


            if window["width"] < 500:

                continue


            if window["height"] < 300:

                continue



            self.hwnd = (
                window["hwnd"]
            )


            print(
                "VENTANA SELECCIONADA POR TITULO:"
            )

            print(
                window
            )


            return True



        print(
            "No se encontro ventana por titulo"
        )


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

            "width": right - left,

            "height": bottom - top

        }



    # =====================================
    # Título actual
    # =====================================

    def get_title(self):

        if self.hwnd is None:

            return None


        return win32gui.GetWindowText(
            self.hwnd
        )