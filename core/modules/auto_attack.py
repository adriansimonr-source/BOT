import time

from core.modules.base_module import BaseModule



class AutoAttack(BaseModule):


    def __init__(
        self,
        input_manager,
        target_rules=None
    ):

        super().__init__(
            "Auto Attack",
            interval_ms=50
        )


        self.input = input_manager

        self.target_rules = target_rules


        self.key = "R"


        self.attack_interval = 250


        self.last_attack = None


        self._active_target = None






    # =====================================
    # CONFIG
    # =====================================


    def configure(
        self,
        right_panel,
        center_panel
    ):


        card = right_panel.auto_attack


        self.key = card.key()


        self.attack_interval = card.interval()



        if card.is_enabled():

            self.enable()

        else:

            self.disable()







    # =====================================
    # START
    # =====================================


    def on_start(self):

        super().on_start()


        self.last_attack = None

        self._active_target = None







    # =====================================
    # UPDATE
    # =====================================


    def update(
        self,
        state
    ):


        target = state.target



        if not self._is_attack_allowed(
            target
        ):

            return False





        self._update_target_identity(
            target
        )





        now = (
            time.perf_counter()
            *
            1000
        )



        if (
            self.last_attack is not None
            and
            now - self.last_attack
            <
            self.attack_interval
        ):

            return False





        if self.input.press(
            self.key
        ):


            self.last_attack = now


            print(
                "[AUTO ATTACK]",
                self.key
            )


            return True




        return False







    # =====================================
    # VALIDATION
    # =====================================


    def _is_attack_allowed(
        self,
        target
    ):


        # No target seleccionado

        if not target.exists:

            return False





        # Si no hay reglas activas:

        # atacar directamente

        if self.target_rules is None:

            return True



        if not self.target_rules.has_filters():

            return True






        # Hay filtros activos

        return self.target_rules.is_allowed(
            target
        )








    # =====================================
    # TARGET TRACKING
    # =====================================


    def _update_target_identity(
        self,
        target
    ):


        selection_id = getattr(
            target,
            "selection_id",
            0
        )



        name = str(
            target.name or ""
        ).strip().casefold()



        identity = (

            ("selection", selection_id)

            if selection_id

            else

            ("name", name)

        )



        if identity != self._active_target:


            self._active_target = identity


            # nuevo objetivo

            self.last_attack = None