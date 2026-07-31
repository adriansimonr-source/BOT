import psutil

from core.managers.window_manager import WindowManager
from core.managers.config_manager import ConfigManager
from core.managers.game_profile_manager import GameProfileManager



class ProcessManager:

    def __init__(self):

        self.config = ConfigManager()

        self.game_profiles = GameProfileManager()


        active_game = self.config.get(
            "active_game"
        )


        if active_game:

            self.game_profiles.set_active_game(
                active_game
            )


        self.process = None

        self.pid = None

        self.name = None


        self.window_title = None


        self.window_manager = WindowManager()



    def find_process(
        self,
        process_name=None
    ):

        self.disconnect()


        if process_name is None:

            process_name = (
                self.game_profiles.get_process()
            )


        if process_name is None:

            return False



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

                    self.pid = process.info["pid"]

                    self.name = name


                    window_title = (
                        self.game_profiles.get_window()
                    )


                    found_window = (
                        self.window_manager.find_window_by_pid(
                            self.pid,
                            window_title
                        )
                    )


                    if not found_window:

                        found_window = (
                            self.window_manager.find_window_by_title(
                                window_title
                            )
                        )


                    if found_window:

                        self.window_title = window_title


                    return True



            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):

                continue



        return False





    def set_game(
        self,
        game_id
    ):

        return self.game_profiles.set_active_game(
            game_id
        )





    def get_active_game(self):

        return (
            self.game_profiles.get_active_game()
        )





    def find_window_only(
        self,
        title=None
    ):

        if title is None:

            title = self.game_profiles.get_window()


        found = (
            self.window_manager.find_window_by_title(
                title
            )
        )


        if found:

            self.window_title = title


        return found





    def is_connected(self):

        if self.process is None:

            return False


        try:

            return self.process.is_running()


        except psutil.Error:

            return False





    def get_pid(self):

        return self.pid



    def get_name(self):

        return self.name



    def get_process(self):

        return self.process





    def has_window(self):

        return (
            self.window_manager.hwnd is not None
        )





    def get_window_position(self):

        return (
            self.window_manager.get_position()
        )





    def get_window_handle(self):

        return (
            self.window_manager.hwnd
        )





    def get_window_title(self):

        return self.window_title





    def get_configured_process(self):

        return (
            self.game_profiles.get_process()
        )





    def get_configured_window(self):

        return (
            self.game_profiles.get_window()
        )





    def get_available_games(self):

        return (
            self.game_profiles.get_games()
        )





    def disconnect(self):

        self.process = None

        self.pid = None

        self.name = None

        self.window_title = None

        self.window_manager.hwnd = None