import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.bot_engine import BotEngine, BotState
from core.models.target_rules import TargetDecision, TargetRules
from core.modules.auto_attack import AutoAttack
from core.modules.auto_consumables import AutoConsumables
from core.modules.auto_heal import AutoHeal
from core.modules.auto_loot import AutoLoot
from core.modules.auto_target import AutoTarget
from core.modules.rotation_manager import RotationManager, SkillConfig


class FakeInput:

    def __init__(self):
        self.keys = []
        self.hold_times = []

    def press(self, key, hold_ms=None):
        self.keys.append(key)
        self.hold_times.append(hold_ms)
        return True

    def update(self):
        pass


class ScriptedInput(FakeInput):

    def __init__(self, outcomes):
        super().__init__()
        self.outcomes = iter(outcomes)

    def press(self, key, hold_ms=None):
        self.keys.append(key)
        self.hold_times.append(hold_ms)
        return next(self.outcomes)


def create_state(
    *,
    target_exists=False,
    target_name="",
    target_hp=0,
    target_hp_valid=False,
    target_hp_observed_at=None,
    selection_id=0,
    hp=100,
    mp=100,
    navigation_active=False,
):
    return SimpleNamespace(
        target=SimpleNamespace(
            exists=target_exists,
            name=target_name,
            hp_percent=target_hp,
            hp_valid=target_hp_valid,
            hp_observed_at=target_hp_observed_at,
            level=1,
            selection_id=selection_id,
        ),
        player=SimpleNamespace(hp_percent=hp, mp_percent=mp),
        in_combat=target_exists,
        navigation_active=navigation_active,
    )


class AutomationModuleTests(unittest.TestCase):

    def test_auto_target_selects_when_target_is_missing(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())

        module.update(create_state())

        self.assertEqual(input_manager.keys, ["E"])

    def test_auto_target_skips_ignored_target(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["ignored"], enabled=True)
        module = AutoTarget(input_manager, rules)

        module.update(
            create_state(target_exists=True, target_name="Ignored", target_hp=100)
        )

        self.assertEqual(input_manager.keys, ["E"])

    def test_ignored_target_is_retried_after_settling_and_never_attacked(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="Ignored",
            target_hp=100,
            selection_id=1,
        )

        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            target_module.update(state)
        attack_module.update(state)
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.1):
            target_module.update(state)
        attack_module.update(state)
        with patch("core.modules.auto_target.time.perf_counter", return_value=2.0):
            target_module.update(state)
        attack_module.update(state)
        with patch("core.modules.auto_target.time.perf_counter", return_value=5.0):
            target_module.update(state)
        attack_module.update(state)

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_attack_filter_does_not_depend_on_an_auto_target_tick(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="Ignored",
            target_hp=100,
            selection_id=11,
        )

        attack_module.update(state)

        self.assertEqual(input_manager.keys, [])

    def test_unknown_target_hp_allows_attack_and_skills_without_cycling(self):
        input_manager = FakeInput()
        state = create_state(
            target_exists=True,
            target_name="Enemy",
            target_hp=0,
            target_hp_valid=False,
            target_hp_observed_at=None,
            selection_id=1,
        )

        target_module = AutoTarget(input_manager, TargetRules())
        attack_module = AutoAttack(input_manager, TargetRules())
        rotation = RotationManager(input_manager)
        rotation.skills = [SkillConfig(True, "1", 0)]

        with patch("core.modules.auto_target.time.perf_counter", return_value=0.0):
            target_module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=0.0):
            attack_module.update(state)
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=0.0):
            rotation.update(state)

        self.assertEqual(input_manager.keys, ["R", "1"])

    def test_auto_attack_requires_an_allowed_target(self):
        input_manager = FakeInput()
        module = AutoAttack(input_manager, TargetRules())

        with patch("core.modules.auto_attack.time.perf_counter", return_value=10.0):
            module.update(create_state())
        with patch("core.modules.auto_attack.time.perf_counter", return_value=10.01):
            module.update(
                create_state(target_exists=True, target_name="Enemy", target_hp=0)
            )

        self.assertEqual(input_manager.keys, ["R"])

    def test_auto_attack_respects_blacklist_and_allows_other_names(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Enemy"], enabled=True)
        module = AutoAttack(input_manager, rules)

        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            module.update(
                create_state(
                    target_exists=True,
                    target_name="Enemy",
                    selection_id=1,
                )
            )
            module.update(
                create_state(
                    target_exists=True,
                    target_name="Normal",
                    selection_id=2,
                )
            )
            module.update(
                create_state(
                    target_exists=True,
                    target_name="",
                    selection_id=3,
                )
            )

        self.assertEqual(input_manager.keys, ["R", "R"])

    def test_auto_attack_is_immediate_then_respects_its_interval(self):
        input_manager = FakeInput()
        module = AutoAttack(input_manager, TargetRules())
        state = create_state(target_exists=True, target_name="Enemy")

        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.25):
            module.update(state)

        self.assertEqual(input_manager.keys, ["R", "R"])

    def test_auto_attack_is_immediate_for_each_new_target(self):
        input_manager = FakeInput()
        module = AutoAttack(input_manager, TargetRules())

        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            module.update(
                create_state(target_exists=True, target_name="Enemy A")
            )
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            module.update(
                create_state(target_exists=True, target_name="Enemy B")
            )

        self.assertEqual(input_manager.keys, ["R", "R"])

    def test_auto_attack_reads_its_configured_interval(self):
        module = AutoAttack(FakeInput(), TargetRules())
        card = SimpleNamespace(
            key=lambda: "R",
            interval=lambda: 725,
            is_enabled=lambda: True,
        )

        module.configure(SimpleNamespace(auto_attack=card), None)

        self.assertEqual(module.attack_interval, 725)

    def test_auto_attack_does_not_repeat_when_same_selection_resolves_its_name(self):
        input_manager = FakeInput()
        module = AutoAttack(input_manager, TargetRules())
        module.attack_interval = 950
        pending_identity = create_state(
            target_exists=True,
            target_name="",
            selection_id=7,
        )
        resolved_identity = create_state(
            target_exists=True,
            target_name="Enemy",
            selection_id=7,
        )

        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            module.update(pending_identity)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.3):
            module.update(resolved_identity)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.949):
            module.update(resolved_identity)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.95):
            module.update(resolved_identity)

        self.assertEqual(input_manager.keys, ["R", "R"])

    def test_active_blacklist_allows_unknown_identity(self):
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)

        decision = rules.evaluate(
            create_state(target_exists=True, target_name="").target
        )

        self.assertIs(decision, TargetDecision.ALLOW)

    def test_blacklist_filters_selection_and_attack_case_insensitively(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)

        ignored_target = create_state(
            target_exists=True,
            target_name="iGnOrEd",
            target_hp=100,
            selection_id=1,
        )
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            target_module.update(ignored_target)
        attack_module.update(ignored_target)

        self.assertEqual(input_manager.keys, ["E"])

        allowed_target = create_state(
            target_exists=True,
            target_name="Normal",
            target_hp=100,
            selection_id=2,
        )
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.1):
            target_module.update(allowed_target)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            attack_module.update(allowed_target)

        self.assertEqual(input_manager.keys, ["E", "R"])

    def test_allowed_target_is_held_while_damage_progresses(self):
        input_manager = FakeInput()
        rules = TargetRules()
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="Boss",
            target_hp=100,
            target_hp_valid=True,
            target_hp_observed_at=0.0,
            selection_id=7,
        )

        with patch("core.modules.auto_target.time.perf_counter", return_value=0.0):
            target_module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            attack_module.update(state)

        state.target.hp_percent = 50
        state.target.hp_observed_at = 5.0
        with patch("core.modules.auto_target.time.perf_counter", return_value=5.0):
            target_module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.25):
            attack_module.update(state)

        state.target.exists = False
        with patch("core.modules.auto_target.time.perf_counter", return_value=6.0):
            target_module.update(state)
        attack_module.update(state)

        self.assertEqual(input_manager.keys, ["R", "R", "E"])

    def test_zero_selection_id_still_applies_blacklist_filter(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="Normal",
            target_hp=100,
            selection_id=0,
        )

        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            target_module.update(state)
        state.target.name = "Ignored"
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.1):
            target_module.update(state)
        attack_module.update(state)

        self.assertEqual(input_manager.keys, ["E"])

    def test_unknown_name_is_allowed_then_resolved_ignored_name_is_rejected(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="",
            target_hp=100,
            selection_id=9,
        )

        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            target_module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            attack_module.update(state)

        state.target.name = "Ignored"
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.1):
            target_module.update(state)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            attack_module.update(state)

        self.assertEqual(input_manager.keys, ["R", "E"])

    def test_new_allowed_selection_attacks_before_auto_target_updates(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)
        state = create_state(
            target_exists=True,
            target_name="Ignored",
            target_hp=100,
            selection_id=1,
        )

        with patch("core.modules.auto_target.time.perf_counter", return_value=0.0):
            target_module.update(state)
        state.target.selection_id = 2
        state.target.name = "New Target"
        with patch("core.modules.auto_attack.time.perf_counter", return_value=0.1):
            attack_module.update(state)
        with patch("core.modules.auto_target.time.perf_counter", return_value=0.1):
            target_module.update(state)

        self.assertEqual(input_manager.keys, ["E", "R"])

    def test_engine_configures_only_blacklist_for_target_and_attack(self):
        enabled = SimpleNamespace(isChecked=lambda: True)
        panel = SimpleNamespace(
            get_ignored_targets=lambda: ["Ignored", "ignored"],
            ignore_targets=enabled,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.target_rules = TargetRules()
        engine.modules = []

        engine.configure(panel, None)

        self.assertEqual(engine.target_rules.blacklist, ["ignored"])
        self.assertTrue(engine.target_rules.blacklist_enabled)
        self.assertTrue(engine.target_rules.has_filters())

        input_manager = FakeInput()
        target_module = AutoTarget(input_manager, engine.target_rules)
        attack_module = AutoAttack(input_manager, engine.target_rules)
        rejected = create_state(
            target_exists=True,
            target_name="IGNORED",
            target_hp=100,
            selection_id=1,
        )
        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            target_module.update(rejected)
        attack_module.update(rejected)

        unknown = create_state(
            target_exists=True,
            target_name="",
            target_hp=100,
            selection_id=2,
        )
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            attack_module.update(unknown)

        self.assertEqual(input_manager.keys, ["E", "R"])

    def test_pause_releases_long_inputs_and_resume_enables_them(self):
        calls = []
        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.RUNNING
        engine.input_manager = SimpleNamespace(
            disable=lambda: calls.append("disable"),
            enable=lambda: calls.append("enable"),
        )

        engine.pause()
        engine.resume()

        self.assertEqual(calls, ["disable", "enable"])
        self.assertEqual(engine.state, BotState.RUNNING)

    def test_empty_checked_blacklist_does_not_block_unknown_targets(self):
        enabled = SimpleNamespace(isChecked=lambda: True)
        panel = SimpleNamespace(
            get_ignored_targets=lambda: [],
            ignore_targets=enabled,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.target_rules = TargetRules()
        engine.modules = []

        engine.configure(panel, None)

        self.assertFalse(engine.target_rules.blacklist_enabled)
        self.assertFalse(engine.target_rules.has_filters())
        self.assertIs(
            engine.target_rules.evaluate(
                create_state(target_exists=True, target_name="").target
            ),
            TargetDecision.ALLOW,
        )

    def test_auto_loot_waits_five_seconds_after_target_disappears(self):
        input_manager = FakeInput()
        module = AutoLoot(input_manager)
        module.loot_interval = 500

        with patch("core.modules.auto_loot.time.perf_counter", return_value=0.0):
            module.on_start()
        with patch("core.modules.auto_loot.time.perf_counter", return_value=1.0):
            module.update(create_state(target_exists=True))
        with patch("core.modules.auto_loot.time.perf_counter", return_value=2.0):
            module.update(create_state())
        with patch("core.modules.auto_loot.time.perf_counter", return_value=6.999):
            module.update(create_state())
        with patch("core.modules.auto_loot.time.perf_counter", return_value=7.0):
            module.update(create_state())
        with patch("core.modules.auto_loot.time.perf_counter", return_value=7.499):
            module.update(create_state())
        with patch("core.modules.auto_loot.time.perf_counter", return_value=7.5):
            module.update(create_state())

        self.assertEqual(input_manager.keys, ["F", "F"])

    def test_auto_loot_never_runs_with_a_selected_target(self):
        input_manager = FakeInput()
        module = AutoLoot(input_manager)
        module._no_target_since = 0.0

        with patch("core.modules.auto_loot.time.perf_counter", return_value=10.0):
            module.update(create_state(target_exists=True))

        self.assertEqual(input_manager.keys, [])

    def test_loot_and_target_are_not_sent_in_the_same_engine_cycle(self):
        input_manager = FakeInput()
        rules = TargetRules()
        auto_loot = AutoLoot(input_manager)
        auto_target = AutoTarget(input_manager, rules)
        auto_loot.set_interval(0)
        auto_target.set_interval(0)
        auto_loot._no_target_since = 0.0

        state = create_state()
        state.connected = True
        game_state_manager = SimpleNamespace(
            update=lambda: None,
            get_state=lambda: state,
            update_auxiliary=lambda: None,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.RUNNING
        engine.game_state_manager = game_state_manager
        engine.input_manager = input_manager
        engine.modules = [auto_loot, auto_target]

        with patch("core.modules.auto_loot.time.perf_counter", return_value=10.0):
            engine.update()

        self.assertEqual(input_manager.keys, ["F"])

    def test_auto_pot_uses_hp_and_auto_mp_uses_mp(self):
        input_manager = FakeInput()
        module = AutoConsumables(input_manager)
        module.pot1_enabled = True
        module.mp_enabled = True
        module.update(create_state(hp=0, mp=0))
        module.update(create_state(hp=20, mp=100))

        self.assertEqual(input_manager.keys, ["F8"])

        input_manager.keys.clear()
        module.last_pot1_use = None
        module.last_mp_use = None
        module.update(create_state(hp=100, mp=20))

        self.assertEqual(input_manager.keys, ["F9"])

    def test_auto_resources_are_immediate_and_failed_send_keeps_interval_due(self):
        configurations = (
            ("F8", "pot1_enabled", "pot1_interval", create_state(hp=20, mp=100)),
            ("F9", "mp_enabled", "mp_interval", create_state(hp=100, mp=20)),
        )
        for key, enabled_attribute, interval_attribute, state in configurations:
            with self.subTest(key=key):
                input_manager = ScriptedInput([False, True, True])
                module = AutoConsumables(input_manager)
                setattr(module, enabled_attribute, True)
                setattr(module, interval_attribute, 2000)
                module.on_start()

                with patch(
                    "core.modules.auto_consumables.time.perf_counter",
                    return_value=0.0,
                ):
                    module.update(state)
                with patch(
                    "core.modules.auto_consumables.time.perf_counter",
                    return_value=0.05,
                ):
                    module.update(state)
                with patch(
                    "core.modules.auto_consumables.time.perf_counter",
                    return_value=2.049,
                ):
                    module.update(state)
                with patch(
                    "core.modules.auto_consumables.time.perf_counter",
                    return_value=2.05,
                ):
                    module.update(state)

                self.assertEqual(input_manager.keys, [key, key, key])

    def test_auto_heal_uses_f10_below_hp_threshold(self):
        input_manager = FakeInput()
        module = AutoHeal(input_manager)
        module.enable()

        module.update(create_state(hp=0))
        module.update(create_state(hp=20))

        self.assertEqual(input_manager.keys, ["F10"])

    def test_auto_heal_is_immediate_and_failed_send_does_not_start_interval(self):
        input_manager = ScriptedInput([False, True, True])
        module = AutoHeal(input_manager)
        module.interval = 2000
        module.on_start()
        state = create_state(hp=20)

        with patch("core.modules.auto_heal.time.perf_counter", return_value=0.0):
            module.update(state)
        with patch("core.modules.auto_heal.time.perf_counter", return_value=0.05):
            module.update(state)
        with patch("core.modules.auto_heal.time.perf_counter", return_value=2.049):
            module.update(state)
        with patch("core.modules.auto_heal.time.perf_counter", return_value=2.05):
            module.update(state)

        self.assertEqual(input_manager.keys, ["F10", "F10", "F10"])

    def test_rotation_depends_only_on_its_timer_even_during_navigation(self):
        input_manager = FakeInput()
        module = RotationManager(input_manager)
        module.skills = [SkillConfig(True, "1", 500)]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.0):
            module.on_start()

        state = create_state(navigation_active=True)
        state.connected = True
        game_state_manager = SimpleNamespace(
            update=lambda: None,
            get_state=lambda: state,
            update_auxiliary=lambda: None,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.RUNNING
        engine.game_state_manager = game_state_manager
        engine.input_manager = input_manager
        engine.modules = [module]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.5):
            engine.update()

        self.assertEqual(input_manager.keys, ["1"])

    def test_navigation_blocks_loot_and_target_but_allows_attack(self):
        input_manager = FakeInput()
        rules = TargetRules()
        auto_loot = AutoLoot(input_manager)
        auto_target = AutoTarget(input_manager, rules)
        auto_attack = AutoAttack(input_manager, rules)
        blocked_updates = []
        auto_loot.update = lambda state: blocked_updates.append("loot")
        auto_target.update = lambda state: blocked_updates.append("target")

        state = create_state(
            target_exists=True,
            target_name="Enemy",
            selection_id=1,
            navigation_active=True,
        )
        state.connected = True
        game_state_manager = SimpleNamespace(
            update=lambda: None,
            get_state=lambda: state,
            update_auxiliary=lambda: None,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.state = BotState.RUNNING
        engine.game_state_manager = game_state_manager
        engine.input_manager = input_manager
        engine.modules = [auto_loot, auto_target, auto_attack]

        engine.update()

        self.assertEqual(blocked_updates, [])
        self.assertEqual(input_manager.keys, ["R"])

    def test_rotation_prioritizes_the_shortest_configured_interval(self):
        input_manager = FakeInput()
        module = RotationManager(input_manager)
        module.skills = [
            SkillConfig(True, "1", 500),
            SkillConfig(True, "2", 1000),
        ]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.0):
            module.on_start()
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.4):
            module.update(create_state(target_exists=True, target_hp=0))
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.5):
            module.update(create_state(target_exists=True, target_hp=0))
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=11.0):
            module.update(create_state(target_exists=True, target_hp=0))
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=11.025):
            module.update(create_state(target_exists=True, target_hp=0))

        self.assertEqual(input_manager.keys, ["1", "1", "2"])

    def test_rotation_uses_gui_interval_before_the_oldest_deadline(self):
        input_manager = FakeInput()
        module = RotationManager(input_manager)
        module.skills = [
            SkillConfig(True, "1", 500, last_cast=2100),
            SkillConfig(True, "F1", 2000, last_cast=0),
        ]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=3.0):
            module.update(create_state())

        self.assertEqual(input_manager.keys, ["1"])
        self.assertEqual(input_manager.hold_times, [25])

    def test_rotation_resolves_equal_intervals_one_skill_per_cycle(self):
        input_manager = FakeInput()
        module = RotationManager(input_manager)
        module.skills = [
            SkillConfig(True, "1", 500),
            SkillConfig(True, "F1", 500),
        ]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=20.0):
            module.on_start()
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=20.5):
            module.update(create_state(target_exists=True))

        self.assertEqual(input_manager.keys, ["1"])

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=20.55):
            module.update(create_state(target_exists=True))

        self.assertEqual(input_manager.keys, ["1", "F1"])

    def test_rotation_failed_send_does_not_start_skill_interval(self):
        input_manager = ScriptedInput([False, True, True])
        module = RotationManager(input_manager)
        module.skills = [SkillConfig(True, "1", 500)]

        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.0):
            module.on_start()
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.5):
            module.update(SimpleNamespace())
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=10.55):
            module.update(SimpleNamespace())
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=11.049):
            module.update(SimpleNamespace())
        with patch("core.modules.rotation_manager.time.perf_counter", return_value=11.05):
            module.update(SimpleNamespace())

        self.assertEqual(input_manager.keys, ["1", "1", "1"])

    def test_rotation_configures_only_checked_skills(self):
        input_manager = FakeInput()
        module = RotationManager(input_manager)
        enabled_card = SimpleNamespace(
            is_enabled=lambda: True,
            skill_number=lambda: "1",
            time=lambda: 500,
        )
        disabled_card = SimpleNamespace(
            is_enabled=lambda: False,
            skill_number=lambda: "2",
            time=lambda: 250,
        )

        module.configure(None, SimpleNamespace(skills=[enabled_card, disabled_card]))

        self.assertEqual([skill.key for skill in module.skills], ["1"])

    def test_rotation_reads_numeric_and_function_key_intervals(self):
        cards = [
            SimpleNamespace(
                is_enabled=lambda: True,
                skill_number=lambda key=key: key,
                time=lambda interval=interval: interval,
            )
            for key, interval in (
                ("1", 500),
                ("9", 900),
                ("F1", 1100),
                ("F9", 1900),
            )
        ]
        module = RotationManager(FakeInput())

        module.configure(None, SimpleNamespace(skills=cards))

        self.assertEqual(
            [(skill.key, skill.cooldown) for skill in module.skills],
            [("1", 500), ("9", 900), ("F1", 1100), ("F9", 1900)],
        )


if __name__ == "__main__":
    unittest.main()
