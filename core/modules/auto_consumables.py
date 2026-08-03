import time

from core.modules.base_module import BaseModule



class AutoConsumables(BaseModule):


    def __init__(
        self,
        input_manager
    ):

        super().__init__(
            "Auto Consumables"
        )


        self.input = input_manager



        self.hp_enabled = False
        self.hp_key = "F8"
        self.hp_threshold = 40
        self.hp_interval = 2000
        self.last_hp_use = 0



        self.mp_enabled = False
        self.mp_key = "F9"
        self.mp_threshold = 30
        self.mp_interval = 2000
        self.last_mp_use = 0






    def configure(
        self,
        right_panel,
        center_panel
    ):


        self.hp_enabled = (
            right_panel.hp_potion.is_enabled()
        )


        self.hp_key = (
            right_panel.hp_potion.key()
        )


        self.hp_threshold = (
            right_panel.hp_potion.threshold()
        )


        self.hp_interval = (
            right_panel.hp_potion.interval()
        )





        self.mp_enabled = (
            right_panel.mp_potion.is_enabled()
        )


        self.mp_key = (
            right_panel.mp_potion.key()
        )


        self.mp_threshold = (
            right_panel.mp_potion.threshold()
        )


        self.mp_interval = (
            right_panel.mp_potion.interval()
        )







    def is_enabled(self):

        return (
            self.hp_enabled
            or
            self.mp_enabled
        )







    def on_start(self):

        self.last_hp_use = 0

        self.last_mp_use = 0







    def update(
        self,
        state
    ):


        player = state.player


        now = time.time() * 1000






        if self.hp_enabled:


            if player.hp_percent <= self.hp_threshold:


                if now - self.last_hp_use >= self.hp_interval:


                    self.use_hp_potion()

                    self.last_hp_use = now







        if self.mp_enabled:


            if player.mp_percent <= self.mp_threshold:


                if now - self.last_mp_use >= self.mp_interval:


                    self.use_mp_potion()

                    self.last_mp_use = now







    def use_hp_potion(self):

        self.input.press(
            self.hp_key
        )







    def use_mp_potion(self):

        self.input.press(
            self.mp_key
        )