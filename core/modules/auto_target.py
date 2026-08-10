import time

from core.modules.base_module import BaseModule


class AutoTarget(BaseModule):


    def __init__(
        self,
        input_manager,
        target_rules
    ):

        super().__init__(
            "Auto Target",
            interval_ms=50
        )


        self.input = input_manager

        self.target_rules = target_rules


        self.key = "E"

        self.target_interval = 250

        self.last_target = None






    # =====================================
    # CONFIG
    # =====================================


    def configure(
        self,
        right_panel,
        center_panel
    ):


        card = right_panel.auto_target


        self.key = card.key()

        self.target_interval = card.interval()



        if card.is_enabled():

            self.enable()

        else:

            self.disable()






    # =====================================
    # START
    # =====================================


    def on_start(self):

        super().on_start()

        self.last_target = None






    # =====================================
    # UPDATE
    # =====================================


    def update(
        self,
        state
    ):


        target = state.target




        # =================================
        # SIN FILTROS
        # =================================

        if not self.target_rules.has_filters():



            # si no hay objetivo

            if not target.exists:

                return self._press_target()



            return False






        # =================================
        # CON FILTROS
        # =================================


        if not target.exists:

            return self._press_target()



        if self.target_rules.is_allowed(
            target
        ):

            return False





        # objetivo rechazado

        return self._press_target()







    # =====================================
    # PRESS TARGET
    # =====================================


    def _press_target(
        self
    ):


        now = time.perf_counter() * 1000



        if (

            self.last_target is not None

            and

            now - self.last_target

            <

            self.target_interval

        ):

            return False





        if self.input.press(
            self.key
        ):


            self.last_target = now


            print(
                "[AUTO TARGET]",
                self.key
            )


            return True



        return False