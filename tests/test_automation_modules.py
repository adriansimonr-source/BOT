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

    def press(self, key):
        self.keys.append(key)
        return True

    def update(self):
        pass


class ScriptedInput(FakeInput):

    def __init__(self, outcomes):
        super().__init__()
        self.outcomes = iter(outcomes)

    def press(self, key):
        self.keys.append(key)
        return next(self.outcomes)


def create_state(
    *,
    target_exists=False,
    target_name="",
    target_hp=0,
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
        rules.set_blacklist(["ignored"])
        module = AutoTarget(input_manager, rules)

        module.update(
            create_state(target_exists=True, target_name="Ignored", target_hp=100)
        )

        self.assertEqual(input_manager.keys, ["E"])

    def test_auto_target_does_not_depend_on_target_hp(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())

        module.update(
            create_state(target_exists=True, target_name="Enemy", target_hp=0)
        )

        self.assertEqual(input_manager.keys, [])

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

    def test_unknown_identity_is_pending_when_target_name_is_required(self):
        rules = TargetRules()
        rules.set_unique_targets(["Boss"], enabled=True)
        rules.allow_unknown = False

        decision = rules.evaluate(
            create_state(target_exists=True, target_name="").target
        )

        self.assertIs(decision, TargetDecision.PENDING)

    def test_unique_targets_filter_selection_and_attack(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_unique_targets(["Boss"], enabled=True)
        rules.allow_unknown = False
        target_module = AutoTarget(input_manager, rules)
        attack_module = AutoAttack(input_manager, rules)

        wrong_target = create_state(target_exists=True, target_name="Normal")
        target_module.update(wrong_target)
        attack_module.update(wrong_target)

        self.assertEqual(input_manager.keys, ["E"])

        allowed_target = create_state(target_exists=True, target_name="boss")
        target_module.update(allowed_target)
        with patch("core.modules.auto_attack.time.perf_counter", return_value=10.0):
            attack_module.update(allowed_target)

        self.assertEqual(input_manager.keys, ["E", "R"])

    def test_engine_configures_multiple_unique_targets_for_target_and_attack(self):
        enabled = SimpleNamespace(isChecked=lambda: True)
        panel = SimpleNamespace(
            get_ignored_targets=lambda: ["Ignored", "ignored"],
            get_unique_targets=lambda: ["Boss A", "boss a", "Boss B"],
            ignore_targets=enabled,
            unique_targets_checkbox=enabled,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.target_rules = TargetRules()
        engine.modules = []

        engine.configure(panel, None)

        self.assertEqual(engine.target_rules.blacklist, ["ignored"])
        self.assertEqual(
            engine.target_rules.unique_targets,
            ["boss a", "boss b"],
        )
        self.assertTrue(engine.target_rules.unique_targets_enabled)
        self.assertFalse(engine.target_rules.allow_unknown)

        input_manager = FakeInput()
        target_module = AutoTarget(input_manager, engine.target_rules)
        attack_module = AutoAttack(input_manager, engine.target_rules)
        rejected = create_state(target_exists=True, target_name="Normal")
        target_module.update(rejected)
        attack_module.update(rejected)

        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.0):
            attack_module.update(
                create_state(target_exists=True, target_name="BOSS A")
            )
        with patch("core.modules.auto_attack.time.perf_counter", return_value=1.1):
            attack_module.update(
                create_state(target_exists=True, target_name="boss b")
            )

        self.assertEqual(input_manager.keys, ["E", "R", "R"])

    def test_empty_checked_filters_do_not_block_unknown_targets(self):
        enabled = SimpleNamespace(isChecked=lambda: True)
        panel = SimpleNamespace(
            get_ignored_targets=lambda: [],
            get_unique_targets=lambda: [],
            ignore_targets=enabled,
            unique_targets_checkbox=enabled,
        )
        engine = BotEngine.__new__(BotEngine)
        engine.target_rules = TargetRules()
        engine.modules = []

        engine.configure(panel, None)

        self.assertFalse(engine.target_rules.unique_targets_enabled)
        self.assertTrue(engine.target_rules.allow_unknown)

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

    def test_auto_target_waits_for_pending_ocr_until_timeout(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_unique_targets(["Boss"], enabled=True)
        rules.allow_unknown = False
        module = AutoTarget(input_manager, rules)
        state = create_state(target_exists=True, target_name="")

        with patch("core.modules.auto_target.time.perf_counter", return_value=1.0):
            module.update(state)
        timeout = module.UNKNOWN_NAME_TIMEOUT_SECONDS
        with patch(
            "core.modules.auto_target.time.perf_counter",
            return_value=1.0 + timeout - 0.001,
        ):
            module.update(state)
        with patch(
            "core.modules.auto_target.time.perf_counter",
            return_value=1.0 + timeout,
        ):
            module.update(state)

        self.assertEqual(input_manager.keys, ["E"])

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

    def test_rotation_waits_for_each_interval_and_prioritizes_earliest_due(self):
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

        self.assertEqual(input_manager.keys, ["1", "2"])

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


if __name__ == "__main__":
    unittest.main()
