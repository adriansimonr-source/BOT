from enum import Enum, auto

from core.modules.auto_target import AutoTarget
from core.modules.auto_attack import AutoAttack
from core.modules.auto_loot import AutoLoot
from core.modules.auto_consumables import AutoConsumables
from core.modules.auto_heal import AutoHeal
from core.modules.rotation_manager import RotationManager
from core.modules.movement_manager import MovementManager

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

        self.target_rules = self.profile.target_rules

        self.input_manager = InputManager(
            self.game_state_manager
        )

        self.modules = []

        for module in (
            AutoConsumables(self.input_manager),
            AutoHeal(self.input_manager),
            MovementManager(self.input_manager, self.profile.bot_settings),
            AutoLoot(self.input_manager),
            AutoTarget(self.input_manager, self.target_rules),
            AutoAttack(self.input_manager, self.target_rules),
            RotationManager(self.input_manager),
        ):
            self.register_module(module)




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
        center_panel,
        character_group=None,
    ):

        if character_group is not None:
            self.profile.bot_settings.set_mode(
                character_group.get_bot_mode()
            )
            self.profile.bot_settings.set_return_delay(
                character_group.get_quiet_seconds()
            )

        ignored_targets = right_panel.get_ignored_targets()
        ignored_enabled = (
            right_panel.ignore_targets.isChecked()
            and bool(ignored_targets)
        )
        if not ignored_enabled:
            ignored_targets = []
        self.target_rules.set_blacklist(ignored_targets)

        unique_targets = right_panel.get_unique_targets()
        unique_enabled = (
            right_panel.unique_targets_checkbox.isChecked()
            and bool(unique_targets)
        )
        self.target_rules.set_unique_targets(
            unique_targets,
            unique_enabled,
        )
        self.target_rules.allow_unknown = not (
            ignored_enabled or unique_enabled
        )

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

        self.input_manager.enable()

        try:
            self.game_state_manager.start()

            for module in self.modules:

                module.on_start()
        except Exception:
            self.input_manager.disable()
            self.game_state_manager.stop()
            self.state = BotState.STOPPED
            raise

        self.state = BotState.RUNNING


    def stop(self):

        if self.state == BotState.STOPPED:

            return


        self.state = BotState.STOPPED

        self.input_manager.disable()

        self.game_state_manager.stop()


        for module in self.modules:

            module.on_stop()


    def pause(self):

        if self.state != BotState.RUNNING:

            return


        self.state = BotState.PAUSED


    def resume(self):

        if self.state != BotState.PAUSED:

            return


        self.state = BotState.RUNNING


    # ==========================
    # POSITION
    # ==========================


    def lock_player_position(self):

        return self.game_state_manager.lock_player_position()



    def unlock_player_position(self):

        self.game_state_manager.unlock_player_position()



    def refresh_player_position(self):

        self.game_state_manager.refresh_player_position()


    def refresh_player_name(self):

        self.game_state_manager.refresh_player_name()




    # ==========================
    # LOOP
    # ==========================


    def update(self):


        self.input_manager.update()


        if self.state != BotState.RUNNING:

            return



        self.game_state_manager.update()


        state = self.game_state_manager.get_state()

        if not state.connected:
            return

        loot_sent = False
        for module in self.modules:


            if not module.is_enabled():

                continue


            if not module.should_update():

                continue


            if (
                getattr(state, "navigation_active", False)
                and isinstance(
                    module,
                    (AutoLoot, AutoTarget, AutoAttack),
                )
            ):

                continue


            if loot_sent and isinstance(module, AutoTarget):

                continue


            action_sent = module.update(
                state
            )

            if isinstance(module, AutoLoot) and action_sent:

                loot_sent = True


        self.game_state_manager.update_auxiliary()






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
