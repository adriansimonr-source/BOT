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
from core.models.automation_config import config_from_widgets
from core.models.player_profile import PlayerProfile

class BotState(Enum):

    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()

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

        self._modules_active = False

        self.auto_target = AutoTarget(
            self.input_manager,
            self.target_rules
        )

        self.movement_manager = MovementManager(
            self.input_manager,
            self.profile.bot_settings,
            learning_path="data/navigation_learning.json",
            profile_id=self._active_game_id(),
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
            self.movement_manager
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

        self.apply_config(
            config_from_widgets(
                right_panel,
                center_panel,
                character_group,
            )
        )

    def apply_config(self, config):

        movement_manager = getattr(self, "movement_manager", None)
        session_active = getattr(
            self,
            "state",
            BotState.STOPPED,
        ) in (BotState.RUNNING, BotState.PAUSED)

        if movement_manager is not None and not session_active:

            movement_manager.set_learning_profile(
                self._active_game_id()
            )

        if config.bot_mode is not None:

            self.profile.bot_settings.set_mode(
                config.bot_mode
            )

        if config.quiet_seconds is not None:

            self.profile.bot_settings.set_return_delay(
                config.quiet_seconds
            )

        self.target_rules.set_blacklist(

            config.ignored_targets,

            config.ignore_enabled and bool(config.ignored_targets)

        )

        for module in getattr(self, "modules", ()):
            if isinstance(module, RotationManager):
                if config.skills is None:
                    continue
                if session_active:
                    module.merge_config(config.skills)
                else:
                    module.configure(config, config)
                continue

            if isinstance(module, AutoConsumables):
                if config.auto_pot1 is None or config.auto_mp is None:
                    continue
            elif isinstance(module, AutoHeal):
                if config.auto_heal is None:
                    continue
            elif isinstance(module, AutoLoot):
                if config.auto_loot is None:
                    continue
            elif isinstance(module, AutoTarget):
                if config.auto_target is None:
                    continue
            elif isinstance(module, AutoAttack):
                if config.auto_attack is None:
                    continue
            else:
                continue

            module.configure(config, config)

    def _active_game_id(self):

        process_manager = getattr(
            self.game_state_manager,
            "process_manager",
            None,
        )

        getter = getattr(process_manager, "get_active_game", None)

        game = getter() if callable(getter) else None

        return game.get("id") if isinstance(game, dict) else "default"

    def start(self):

        if self.state == BotState.RUNNING:

            return True

        if self.state == BotState.STOPPING:

            return False

        self.input_manager.enable()

        try:

            if self.game_state_manager.start() is False:

                self.input_manager.disable()

                self.state = BotState.STOPPING

                return False

            self._modules_active = True

            for module in self.modules:

                module.on_start()

        except Exception:

            self.input_manager.disable()

            self.state = BotState.STOPPING

            if self.game_state_manager.stop() is not False:

                self._finish_stop()

            raise

        self.state = BotState.RUNNING

        return True

    def request_stop(self):

        self.input_manager.disable()

        requester = getattr(
            self.game_state_manager,
            "request_stop",
            None,
        )

        if callable(requester):

            requester()

    def stop(self):

        stopped = self.game_state_manager.stop()

        if self.state == BotState.STOPPED and stopped is not False:

            return True

        self.state = BotState.STOPPING

        self.input_manager.disable()

        if stopped is False:

            return False

        self._finish_stop()

        return True

    def _finish_stop(self):

        if getattr(self, "_modules_active", False):

            self._modules_active = False

            for module in self.modules:

                module.on_stop()

        self.state = BotState.STOPPED

    def pause(self):

        if self.state != BotState.RUNNING:

            return

        movement_manager = getattr(self, "movement_manager", None)

        if movement_manager is not None:

            movement_manager.suspend("bot_pausado")

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

            movement_manager = getattr(self, "movement_manager", None)

            if movement_manager is not None:

                movement_manager.suspend("desconectado")

            self.game_state_manager.update_auxiliary()

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
