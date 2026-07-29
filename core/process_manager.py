import psutil

from core.managers.window_manager import WindowManager


class ProcessManager:


    def __init__(self):

        # ===============================
        # Datos del proceso
        # ===============================

        self.process = None

        self.pid = None

        self.name = None


        # ===============================
        # Ventana del proceso
        # ===============================

        self.window_manager = WindowManager()



    # =====================================
    # Buscar proceso
    # =====================================

    def find_process(
        self,
        process_name: str
    ):


        self.process = None


        for process in psutil.process_iter(
            [
                "pid",
                "name"
            ]
        ):

            try:

                name = process.info["name"]


                if name == process_name:

                    self.process = process

                    self.pid = (
                        process.info["pid"]
                    )

                    self.name = name


                    # Buscar ventana

                    self.window_manager.find_window_by_pid(
                        self.pid
                    )


                    return True



            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):

                continue



        return False



    # =====================================
    # Estado conexión
    # =====================================

    def is_connected(self):

        if self.process is None:

            return False


        try:

            return (
                self.process.is_running()
            )


        except:

            return False



    # =====================================
    # Información proceso
    # =====================================

    def get_pid(self):

        return self.pid



    def get_name(self):

        return self.name



    def get_process(self):

        return self.process



    # =====================================
    # Información ventana
    # =====================================

    def has_window(self):

        return (
            self.window_manager.hwnd
            is not None
        )



    def get_window_position(self):

        return (
            self.window_manager
            .get_position()
        )



    def get_window_handle(self):

        return (
            self.window_manager.hwnd
        )



    # =====================================
    # Limpiar
    # =====================================

    def disconnect(self):

        self.process = None

        self.pid = None

        self.name = None

        self.window_manager.hwnd = None