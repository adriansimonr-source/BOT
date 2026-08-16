import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from core.managers.entity_cache_manager import EntityCacheManager
from core.models.target_state import TargetState
from core.services.bar_reader import BarReader
from core.services.enemy_monitor import EnemyMonitor


_DEFAULT_HP = object()


class PendingFuture:

    def done(self):
        return False


class CompletedFuture:

    def __init__(self, result):
        self._result = result

    def done(self):
        return True

    def result(self):
        return self._result


class RecordingExecutor:

    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        self.calls.append((function, args))
        return PendingFuture()


class EnemyMonitorTests(unittest.TestCase):

    def test_configured_enemy_area_avoids_full_frame_search_on_miss(self):
        full_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        search_image = np.zeros((300, 540, 3), dtype=np.uint8)
        search_area = {"x": 900, "y": 740, "width": 540, "height": 300}
        detector = SimpleNamespace(detect=MagicMock(return_value=None))
        resolver = SimpleNamespace(crop=MagicMock(return_value=search_image))
        templates = SimpleNamespace(get=lambda name: search_area)
        monitor, _ = self.create_monitor(anchor=None)
        monitor.detector = detector
        monitor.resolver = resolver
        monitor.templates = templates

        detection = monitor._detect_in_search_area(
            full_image,
            object(),
            "enemy_search_area",
        )

        self.assertIsNone(detection)
        detector.detect.assert_called_once_with(search_image, unittest.mock.ANY)

    @staticmethod
    def create_monitor(
        *,
        anchor,
        enemy_name=None,
        executor=None,
        name_matcher=None,
        has_hp_bar=True,
        hp_percent=_DEFAULT_HP,
        database=None,
    ):
        if hp_percent is _DEFAULT_HP:
            hp_percent = 50 if has_hp_bar else None
        detector = SimpleNamespace(detect=lambda image, template: anchor)
        resolver = SimpleNamespace(
            resolve=lambda detection, template: object(),
            crop=lambda image, region: np.zeros((2, 2, 3), dtype=np.uint8),
        )
        templates = SimpleNamespace(
            get=lambda name: {
                "enemy_anchor": object(),
                "enemy_hud": object(),
                "enemy_name": {"x": 0, "y": 0, "width": 1, "height": 1},
                "enemy_level": None,
                "enemy_hp": {"x": 0, "y": 0, "width": 1, "height": 1},
            }.get(name)
        )
        if name_matcher is None:
            name_matcher = SimpleNamespace(
                read_enemy_name=lambda image: enemy_name
            )
        cache = EntityCacheManager()
        if database is None:
            database = SimpleNamespace(
                resolve_enemy_name=lambda name: name,
                register_enemy_seen=lambda name: None,
                resolve_item_name=lambda name: name,
                register_item_seen=lambda name: None,
            )
        monitor = EnemyMonitor(
            detector,
            resolver,
            SimpleNamespace(read_enemy_hp=lambda image: hp_percent),
            templates,
            name_matcher,
            cache,
            database,
            executor=executor,
            target_validator=SimpleNamespace(
                has_red_bar=lambda image: has_hp_bar
            ),
        )
        return monitor, cache

    def test_missing_target_clears_all_previous_target_state(self):
        monitor, _ = self.create_monitor(anchor=None)
        target = TargetState()
        target.exists = True
        target.name = "Previous"
        target.level = 20
        target.hp_percent = 80

        monitor.update(MagicMock(), target)

        self.assertFalse(target.exists)
        self.assertEqual(target.name, "")
        self.assertEqual(target.level, 0)
        self.assertEqual(target.hp_percent, 0)

    def test_two_transient_hud_misses_preserve_the_selected_target(self):
        monitor, _ = self.create_monitor(anchor=object(), enemy_name="Bongbo")
        target = TargetState()
        monitor.update(MagicMock(), target)
        selection_id = target.selection_id
        monitor.detector.detect = MagicMock(return_value=None)

        monitor.update(MagicMock(), target)
        monitor.update(MagicMock(), target)

        self.assertTrue(target.exists)
        self.assertEqual(target.selection_id, selection_id)

        monitor.update(MagicMock(), target)

        self.assertFalse(target.exists)
        self.assertEqual(target.selection_id, selection_id)

    def test_anchor_search_reuses_the_last_hud_position(self):
        monitor, _ = self.create_monitor(anchor=None)
        template_image = np.full((20, 30, 3), 35, dtype=np.uint8)
        template_image[5:15, 7:25] = (10, 15, 210)
        template = SimpleNamespace(
            image=template_image,
            threshold=0.75,
            name="enemy_anchor",
            type="anchor",
        )
        full_detection = {
            "x": 100,
            "y": 50,
            "width": 30,
            "height": 20,
        }
        local_detection = {
            "x": 24,
            "y": 24,
            "width": 30,
            "height": 20,
        }
        monitor.bar_reader = BarReader()
        monitor.detector = SimpleNamespace(
            detect=MagicMock(side_effect=[full_detection, local_detection]),
        )
        image = np.zeros((200, 300, 3), dtype=np.uint8)

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            side_effect=[1.0, 1.1],
        ):
            first = monitor._detect_anchor(image, template)
            second = monitor._detect_anchor(image, template)

        self.assertEqual((first["x"], first["y"]), (100, 50))
        self.assertEqual((second["x"], second["y"]), (100, 50))
        local_image = monitor.detector.detect.call_args_list[1].args[0]
        self.assertEqual(local_image.shape[:2], (68, 78))

    def test_forced_anchor_recovery_can_leave_the_cached_roi(self):
        monitor, _ = self.create_monitor(anchor=None)
        template_image = np.full((20, 30, 3), 35, dtype=np.uint8)
        template_image[5:15, 7:25] = (10, 15, 210)
        template = SimpleNamespace(
            image=template_image,
            threshold=0.75,
            name="enemy_anchor",
            type="anchor",
        )
        relocated = {"x": 220, "y": 110, "width": 30, "height": 20}
        monitor.bar_reader = BarReader()
        monitor.anchor_detection = {"x": 100, "y": 50}
        monitor.force_full_anchor_search = True
        monitor.detector = SimpleNamespace(
            detect=MagicMock(return_value=relocated),
        )
        image = np.zeros((200, 300, 3), dtype=np.uint8)

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=1.0,
        ):
            detection = monitor._detect_anchor(image, template)

        self.assertEqual((detection["x"], detection["y"]), (220, 110))
        calls = monitor.detector.detect.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[0].shape[:2], (200, 300))
        self.assertFalse(monitor.force_full_anchor_search)

    def test_failed_forced_search_discards_the_stale_anchor_cache(self):
        monitor, _ = self.create_monitor(anchor=None)
        template_image = np.full((20, 30, 3), 35, dtype=np.uint8)
        template_image[5:15, 7:25] = (10, 15, 210)
        template = SimpleNamespace(
            image=template_image,
            threshold=0.75,
            name="enemy_anchor",
            type="anchor",
        )
        relocated = {"x": 220, "y": 110, "width": 30, "height": 20}
        monitor.bar_reader = BarReader()
        monitor.anchor_detection = {"x": 100, "y": 50}
        monitor.force_full_anchor_search = True
        detect = MagicMock(side_effect=[None, relocated])
        monitor.detector = SimpleNamespace(detect=detect)
        image = np.zeros((200, 300, 3), dtype=np.uint8)

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            side_effect=[1.0, 1.1, 1.6],
        ):
            self.assertIsNone(monitor._detect_anchor(image, template))
            self.assertIsNone(monitor._detect_anchor(image, template))
            detection = monitor._detect_anchor(image, template)

        self.assertEqual(detect.call_count, 2)
        self.assertEqual((detection["x"], detection["y"]), (220, 110))

    def test_bar_reader_measurement_wins_over_validator_false_negative(self):
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Bongbo",
            has_hp_bar=False,
            hp_percent=42,
        )
        target = TargetState()

        monitor.update(MagicMock(), target)

        self.assertTrue(target.exists)
        self.assertTrue(target.hp_valid)
        self.assertEqual(target.hp_percent, 42)

    def test_failed_ocr_does_not_reuse_the_previous_target_name(self):
        monitor, cache = self.create_monitor(anchor=object(), enemy_name=None)
        cache.update_enemy("Allowed Boss", 20)
        target = TargetState()
        target.exists = True
        target.name = "Allowed Boss"
        target.level = 20

        monitor.update(MagicMock(), target)

        self.assertTrue(target.exists)
        self.assertEqual(target.name, "")
        self.assertEqual(target.level, 0)

    def test_target_presence_is_available_while_identity_ocr_is_pending(self):
        executor = RecordingExecutor()
        name_matcher = SimpleNamespace(
            read_enemy_name=MagicMock(side_effect=AssertionError("OCR bloqueante"))
        )
        monitor, _ = self.create_monitor(
            anchor=object(),
            executor=executor,
            name_matcher=name_matcher,
        )
        target = TargetState()

        detected = monitor.update(MagicMock(), target)

        self.assertTrue(detected)
        self.assertTrue(target.exists)
        self.assertTrue(target.visible)
        self.assertTrue(target.identity_pending)
        self.assertEqual(target.selection_id, 1)
        self.assertEqual(len(executor.calls), 1)
        name_matcher.read_enemy_name.assert_not_called()

    def test_failed_identity_ocr_is_rate_limited_per_selection(self):
        name_matcher = SimpleNamespace(
            read_enemy_name=MagicMock(return_value=None),
        )
        monitor, _ = self.create_monitor(
            anchor=object(),
            name_matcher=name_matcher,
        )
        target = TargetState()

        for now in (0.0, 0.1, 1.0, 2.0, 3.0):
            with patch(
                "core.services.enemy_monitor.time.perf_counter",
                return_value=now,
            ):
                monitor.update(MagicMock(), target)

        self.assertEqual(
            name_matcher.read_enemy_name.call_count,
            monitor.MAX_IDENTITY_ATTEMPTS,
        )

    def test_completed_identity_from_an_old_selection_is_discarded(self):
        monitor, _ = self.create_monitor(anchor=object())
        monitor.selection_id = 2
        monitor.identity_future = CompletedFuture(
            (1, None, "Stale Enemy", 20)
        )
        target = TargetState()
        target.exists = True
        target.selection_id = 2

        monitor.poll(target)

        self.assertEqual(target.name, "")
        self.assertEqual(target.level, 0)
        self.assertIsNone(monitor.identity_future)

    def test_stale_worker_result_never_writes_enemy_or_item_database(self):
        for stale_type, current_type, current_selection in (
            (EnemyMonitor.ENTITY_ENEMY, EnemyMonitor.ENTITY_ITEM, 1),
            (EnemyMonitor.ENTITY_ITEM, EnemyMonitor.ENTITY_ITEM, 2),
        ):
            with self.subTest(stale_type=stale_type):
                database = SimpleNamespace(
                    resolve_enemy_name=MagicMock(return_value="Stale Enemy"),
                    register_enemy_seen=MagicMock(return_value=True),
                    resolve_item_name=MagicMock(return_value="Stale Item"),
                    register_item_seen=MagicMock(return_value=True),
                )
                monitor, _ = self.create_monitor(
                    anchor=object(),
                    enemy_name=(
                        "Stale Enemy"
                        if stale_type == EnemyMonitor.ENTITY_ENEMY
                        else "Stale Item"
                    ),
                    database=database,
                )

                worker_result = monitor._read_identity_data(
                    1,
                    None,
                    MagicMock(),
                    stale_type,
                )
                monitor.selection_id = current_selection
                monitor.current_entity_type = current_type
                monitor.identity_future = CompletedFuture(worker_result)
                monitor.poll(TargetState())

                database.resolve_enemy_name.assert_not_called()
                database.register_enemy_seen.assert_not_called()
                database.resolve_item_name.assert_not_called()
                database.register_item_seen.assert_not_called()

    def test_name_without_hp_bar_is_stored_as_item_after_acquisition_grace(self):
        database = SimpleNamespace(
            resolve_enemy_name=MagicMock(
                side_effect=AssertionError("no debe resolver enemigo")
            ),
            register_enemy_seen=MagicMock(),
            resolve_item_name=MagicMock(return_value="Healing Potion"),
            register_item_seen=MagicMock(return_value=True),
        )
        monitor, cache = self.create_monitor(
            anchor=object(),
            enemy_name="Healing Potion",
            has_hp_bar=False,
            database=database,
        )
        cache.update_enemy("Previous Enemy", 10)
        target = TargetState()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.0,
        ):
            self.assertTrue(monitor.update(MagicMock(), target))

        self.assertTrue(target.visible)
        self.assertTrue(target.exists)
        self.assertFalse(target.hp_valid)
        database.register_item_seen.assert_not_called()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=1.0,
        ):
            self.assertTrue(monitor.update(MagicMock(), target))

        self.assertTrue(target.visible)
        self.assertFalse(target.exists)
        self.assertFalse(target.targetable)
        self.assertEqual(target.name, "")
        self.assertEqual(cache.current_enemy_name, "")
        database.resolve_item_name.assert_called_once_with("Healing Potion")
        database.register_item_seen.assert_called_once_with("Healing Potion")
        database.register_enemy_seen.assert_not_called()

    def test_zero_reader_result_stays_unknown_until_a_valid_hp_arrives(self):
        database = SimpleNamespace(
            resolve_enemy_name=MagicMock(return_value="Bongbo"),
            register_enemy_seen=MagicMock(return_value=True),
            resolve_item_name=MagicMock(),
            register_item_seen=MagicMock(),
        )
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Bongbo",
            has_hp_bar=True,
            hp_percent=0,
            database=database,
        )
        target = TargetState()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.0,
        ):
            monitor.update(MagicMock(), target)

        self.assertTrue(target.exists)
        self.assertTrue(target.targetable)
        self.assertFalse(target.hp_valid)
        self.assertEqual(target.hp_percent, 0)
        self.assertEqual(target.name, "")
        selection_id = target.selection_id
        database.register_enemy_seen.assert_not_called()
        database.register_item_seen.assert_not_called()

        monitor.bar_reader.read_enemy_hp = lambda image: 50
        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.1,
        ):
            monitor.update(MagicMock(), target)

        self.assertEqual(target.selection_id, selection_id)
        self.assertTrue(target.hp_valid)
        self.assertEqual(target.hp_percent, 50)
        self.assertEqual(target.name, "Bongbo")
        database.resolve_enemy_name.assert_called_once_with("Bongbo")
        database.register_enemy_seen.assert_called_once_with("Bongbo")
        database.resolve_item_name.assert_not_called()

    def test_persistent_invalid_hp_keeps_visible_target_actionable(self):
        database = SimpleNamespace(
            resolve_enemy_name=MagicMock(),
            register_enemy_seen=MagicMock(),
            resolve_item_name=MagicMock(),
            register_item_seen=MagicMock(),
        )
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Unreadable",
            has_hp_bar=True,
            hp_percent=0,
            database=database,
        )
        target = TargetState()

        for now in (0.0, 1.0):
            with patch(
                "core.services.enemy_monitor.time.perf_counter",
                return_value=now,
            ):
                monitor.update(MagicMock(), target)

        self.assertTrue(target.visible)
        self.assertTrue(target.exists)
        self.assertTrue(target.targetable)
        self.assertFalse(target.hp_valid)
        database.register_enemy_seen.assert_not_called()
        database.register_item_seen.assert_not_called()

    def test_invalid_hp_after_measurement_preserves_presence_and_last_value(self):
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Bongbo",
            has_hp_bar=True,
            hp_percent=50,
        )
        target = TargetState()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.0,
        ):
            monitor.update(MagicMock(), target)

        monitor.bar_reader.read_enemy_hp = MagicMock(return_value=None)
        monitor.target_validator.has_red_bar = MagicMock(return_value=True)
        for now in (0.1, 1.2):
            with patch(
                "core.services.enemy_monitor.time.perf_counter",
                return_value=now,
            ):
                monitor.update(MagicMock(), target)

        self.assertTrue(target.visible)
        self.assertTrue(target.exists)
        self.assertTrue(target.targetable)
        self.assertFalse(target.hp_valid)
        self.assertEqual(target.hp_percent, 50)

    def test_sustained_empty_bar_confirms_death_without_changing_selection(self):
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Bongbo",
            has_hp_bar=True,
            hp_percent=50,
        )
        target = TargetState()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.0,
        ):
            monitor.update(MagicMock(), target)
        selection_id = target.selection_id
        monitor.target_validator.has_red_bar = MagicMock(
            return_value=False
        )
        monitor.bar_reader.read_enemy_hp = MagicMock(return_value=None)

        for now in (0.1, 0.2, 0.3, 0.4):
            with patch(
                "core.services.enemy_monitor.time.perf_counter",
                return_value=now,
            ):
                monitor.update(MagicMock(), target)
            self.assertTrue(target.exists)
            self.assertTrue(target.hp_valid)
            self.assertEqual(target.hp_percent, 50)

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.6,
        ):
            monitor.update(MagicMock(), target)

        self.assertEqual(target.selection_id, selection_id)
        self.assertTrue(target.exists)
        self.assertFalse(target.targetable)
        self.assertTrue(target.hp_valid)
        self.assertEqual(target.hp_percent, 0)

    def test_valid_hp_cancels_an_empty_frame_candidate(self):
        monitor, _ = self.create_monitor(
            anchor=object(),
            enemy_name="Bongbo",
            has_hp_bar=True,
            hp_percent=50,
        )
        target = TargetState()

        with patch(
            "core.services.enemy_monitor.time.perf_counter",
            return_value=0.0,
        ):
            monitor.update(MagicMock(), target)
        monitor.target_validator.has_red_bar = MagicMock(
            side_effect=[False, False, True]
        )
        monitor.bar_reader.read_enemy_hp = MagicMock(
            side_effect=[None, None, 40]
        )

        for now in (0.1, 0.2, 0.3):
            with patch(
                "core.services.enemy_monitor.time.perf_counter",
                return_value=now,
            ):
                monitor.update(MagicMock(), target)

        self.assertTrue(target.exists)
        self.assertTrue(target.targetable)
        self.assertTrue(target.hp_valid)
        self.assertEqual(target.hp_percent, 40)


if __name__ == "__main__":
    unittest.main()
