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

        self.auto_target = AutoTarget(
            self.input_manager,
            self.target_rules
        )

        self.register_module(
            AutoConsumables(
                self.input_manager
            )
        )

        self.register_module(
            AutoHeal(
                self.input_manager
            )
        )

        self.register_module(
            MovementManager(
                self.input_manager,
                self.profile.bot_settings
            )
        )

        self.register_module(
            AutoLoot(
                self.input_manager
            )
        )

        self.register_module(
            self.auto_target
        )

        self.register_module(
            AutoAttack(
                self.input_manager,
                self.target_rules
            )
        )

        self.register_module(
            RotationManager(
                self.input_manager
            )
        )

    def register_module(
        self,
        module
    ):

        self.modules.append(
            module
        )

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

            and

            bool(ignored_targets)

        )

        self.target_rules.set_blacklist(

            ignored_targets,

            ignored_enabled

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

        self.input_manager.disable()

    def resume(self):

        if self.state != BotState.PAUSED:

            return

        self.input_manager.enable()

        self.state = BotState.RUNNING

    def lock_player_position(self):

        return self.game_state_manager.lock_player_position()

    def unlock_player_position(self):

        self.game_state_manager.unlock_player_position()

    def refresh_player_position(self):

        self.game_state_manager.refresh_player_position()

    def update(self):

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

                getattr(
                    state,
                    "navigation_active",
                    False
                )

                and

                isinstance(
                    module,
                    (
                        AutoLoot,
                        AutoTarget
                    )
                )

            ):

                continue

            if (

                loot_sent

                and

                isinstance(
                    module,
                    AutoTarget
                )

            ):

                continue

            action_sent = module.update(
                state
            )

            if (

                isinstance(
                    module,
                    AutoLoot
                )

                and

                action_sent

            ):

                loot_sent = True

        self.game_state_manager.update_auxiliary()

    def is_running(self):

        return self.state == BotState.RUNNING

    def get_state(self):

        return self.state
