from core.input.keyboard_driver import KeyboardDriver
from core.input.window_input_driver import WindowInputDriver




class InputManager:


    def __init__(
        self,
        game_state_manager
    ):

        self.enabled = True

        self.game_state_manager = game_state_manager

        self.keyboard_driver = KeyboardDriver()

        self.window_driver = WindowInputDriver()






    def press(
        self,
        key
    ):


        if not self.enabled:

            return False



        hwnd = None



        try:

            hwnd = (
                self.game_state_manager
                .process_manager
                .get_window_handle()
            )


        except Exception:


            hwnd = None






        if hwnd:


            return self.window_driver.press(
                hwnd,
                key
            )






        return self.keyboard_driver.press(
            key
        )








    def enable(self):

        self.enabled = True






    def disable(self):

        self.enabled = False






    def is_enabled(self):

        return self.enabled