from enum import Enum, auto

from core.modules.auto_target import AutoTarget
from core.modules.auto_attack import AutoAttack
from core.modules.auto_loot import AutoLoot
from core.modules.auto_consumables import AutoConsumables
from core.modules.rotation_manager import RotationManager

from core.input.input_manager import InputManager

from core.managers.game_state_manager import GameStateManager
from core.models.player_profile import PlayerProfile



class BotState(Enum):

    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()



class BotEngine:


    def __init__(
        self,
        game_state_manager: GameStateManager
    ):

        self.state = BotState.STOPPED

        self.game_state_manager = game_state_manager

        self.profile = PlayerProfile()

        self.input_manager = InputManager(
            self.game_state_manager
        )

        self.modules = []


        self.register_module(
            AutoTarget()
        )

        self.register_module(
            AutoAttack()
        )

        self.register_module(
            AutoLoot()
        )

        self.register_module(
            AutoConsumables(
                self.input_manager
            )
        )

        self.register_module(
            RotationManager()
        )




    # ==========================
    # MODULES
    # ==========================


    def register_module(
        self,
        module
    ):

        self.modules.append(
            module
        )



    def unregister_module(
        self,
        module
    ):

        if module in self.modules:

            self.modules.remove(
                module
            )



    def get_modules(self):

        return self.modules



    def get_module(
        self,
        module_type
    ):

        for module in self.modules:

            if isinstance(
                module,
                module_type
            ):

                return module


        return None




    # ==========================
    # PROFILE
    # ==========================


    def get_profile(self):

        return self.profile




    # ==========================
    # CONFIG
    # ==========================


    def configure(
        self,
        right_panel,
        center_panel
    ):

        for module in self.modules:

            if hasattr(
                module,
                "configure"
            ):

                module.configure(
                    right_panel,
                    center_panel
                )




    # ==========================
    # BOT CONTROL
    # ==========================


    def start(self):

        if self.state == BotState.RUNNING:

            return


        self.state = BotState.RUNNING

        self.game_state_manager.start()


        for module in self.modules:

            module.on_start()


        print(
            "Bot iniciado"
        )





    def stop(self):

        if self.state == BotState.STOPPED:

            return


        self.state = BotState.STOPPED

        self.game_state_manager.stop()


        for module in self.modules:

            module.on_stop()


        print(
            "Bot detenido"
        )





    def pause(self):

        if self.state != BotState.RUNNING:

            return


        self.state = BotState.PAUSED


        print(
            "Bot pausado"
        )





    def resume(self):

        if self.state != BotState.PAUSED:

            return


        self.state = BotState.RUNNING


        print(
            "Bot reanudado"
        )





    # ==========================
    # POSITION
    # ==========================


    def lock_player_position(self):

        self.game_state_manager.lock_player_position()



    def unlock_player_position(self):

        self.game_state_manager.unlock_player_position()



    def refresh_player_position(self):

        self.game_state_manager.refresh_player_position()




    # ==========================
    # LOOP
    # ==========================


    def update(self):


        if self.state != BotState.RUNNING:

            return



        self.game_state_manager.update()


        state = self.game_state_manager.get_state()


        player = state.player



        print(
            f"{player.name} "
            f"HP:{player.hp_percent}% "
            f"MP:{player.mp_percent}% "
            f"POS:{player.x},{player.y}"
        )



        for module in self.modules:


            if not module.is_enabled():

                continue


            if not module.should_update():

                continue


            module.update(
                state
            )






    # ==========================
    # STATE
    # ==========================


    def is_running(self):

        return self.state == BotState.RUNNING



    def is_paused(self):

        return self.state == BotState.PAUSED



    def is_stopped(self):

        return self.state == BotState.STOPPED



    def get_state(self):

        return self.state