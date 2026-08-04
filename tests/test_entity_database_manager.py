import tempfile
import unittest

from core.managers.entity_database_manager import EntityDatabaseManager


class EntityDatabaseManagerTests(unittest.TestCase):

    @staticmethod
    def add_enemy(
        manager,
        name,
        encounters=0,
        ignored=False,
        verified=False,
    ):
        manager.database.add_enemy(name)
        enemy = manager.database.enemies[name]
        enemy["encounters"] = encounters
        enemy["ignore"] = ignored
        enemy["verified"] = verified

    def test_known_ocr_aliases_share_one_available_enemy(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "Bongbo", encounters=100)
            self.add_enemy(manager, "Bongbo wf", encounters=2)
            self.add_enemy(manager, "ys Bongbo", encounters=1)
            manager.save()

            reloaded = EntityDatabaseManager(path)

            self.assertEqual(reloaded.resolve_enemy_name("Bongbo wf"), "Bongbo")
            self.assertEqual(reloaded.get_enemy_names(), ["Bongbo"])

    def test_similar_legitimate_names_are_not_merged(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "Goblin A", encounters=3)
            self.add_enemy(manager, "Goblin B", encounters=3)
            manager.save()

            reloaded = EntityDatabaseManager(path)

            self.assertEqual(reloaded.resolve_enemy_name("Goblin A"), "Goblin A")
            self.assertEqual(
                reloaded.get_enemy_names(),
                ["Goblin A", "Goblin B"],
            )

    def test_timer_ocr_is_not_added_or_shown_as_an_enemy(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "4m 59s", encounters=1)
            self.add_enemy(manager, "Bongbo", encounters=3)
            manager.save()

            self.assertIsNone(manager.resolve_enemy_name("4m 12s"))
            self.assertEqual(manager.get_enemy_names(), ["Bongbo"])
            self.assertNotIn("4m 12s", manager.database.enemies)

    def test_reader_detects_new_database_enemies_without_duplicates(self):
        with tempfile.TemporaryDirectory() as path:
            gui_manager = EntityDatabaseManager(path)
            vision_manager = EntityDatabaseManager(path)

            self.assertEqual(vision_manager.resolve_enemy_name("Bongbo"), "Bongbo")
            self.assertEqual(vision_manager.resolve_enemy_name("bONgbo"), "Bongbo")

            self.assertTrue(gui_manager.refresh_enemies())
            self.assertEqual(gui_manager.get_enemy_names(), ["Bongbo"])
            self.assertEqual(len(gui_manager.database.enemies), 1)

    def test_unignore_clears_the_flag_from_all_aliases(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "Bongbo", encounters=100)
            self.add_enemy(
                manager,
                "Bongbo wf",
                encounters=2,
                ignored=True,
            )
            manager.save()

            self.assertEqual(manager.get_ignored_enemy_names(), ["Bongbo"])

            manager.set_enemy_ignored("Bongbo", False)
            reloaded = EntityDatabaseManager(path)

            self.assertEqual(reloaded.get_ignored_enemy_names(), [])
            self.assertTrue(all(
                not enemy.get("ignore", False)
                for enemy in reloaded.database.enemies.values()
            ))

    def test_vision_update_preserves_a_gui_ignore_change(self):
        with tempfile.TemporaryDirectory() as path:
            vision_manager = EntityDatabaseManager(path)
            self.add_enemy(vision_manager, "Bongbo", encounters=1)
            vision_manager.save()
            gui_manager = EntityDatabaseManager(path)

            gui_manager.set_enemy_ignored("Bongbo", True)
            vision_manager.register_enemy_seen("Bongbo")

            reloaded = EntityDatabaseManager(path)
            self.assertTrue(reloaded.should_ignore_enemy("Bongbo"))
            self.assertEqual(
                reloaded.get_enemy("Bongbo")["encounters"],
                2,
            )

    def test_multiple_ignore_changes_are_saved_as_one_batch(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "Alpha", encounters=3)
            self.add_enemy(manager, "Beta", encounters=3)
            manager.save()

            self.assertTrue(
                manager.set_enemies_ignored(
                    ["Alpha", "alpha", "Beta"],
                    True,
                )
            )

            reloaded = EntityDatabaseManager(path)
            self.assertEqual(
                reloaded.get_ignored_enemy_names(),
                ["Alpha", "Beta"],
            )

    def test_unknown_enemy_requires_two_matching_observations(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)

            self.assertEqual(manager.resolve_enemy_name("Bongbo"), "Bongbo")
            self.assertNotIn("Bongbo", manager.database.enemies)

            self.assertEqual(manager.resolve_enemy_name("bONgbo"), "Bongbo")
            self.assertIn("Bongbo", manager.database.enemies)
            self.assertTrue(manager.database.enemies["Bongbo"]["verified"])

    def test_low_confidence_legacy_rows_are_hidden_without_losing_ignored(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)
            self.add_enemy(manager, "Single Reading", encounters=1)
            self.add_enemy(manager, "1 FF gee", encounters=1)
            self.add_enemy(
                manager,
                "Manual Target",
                encounters=1,
                ignored=True,
            )
            self.add_enemy(
                manager,
                "O'Brian-Sombra",
                encounters=1,
                verified=True,
            )
            manager.save()

            reloaded = EntityDatabaseManager(path)

            self.assertEqual(
                reloaded.get_enemy_names(),
                ["Manual Target", "O'Brian-Sombra"],
            )
            self.assertEqual(
                reloaded.get_ignored_enemy_names(),
                ["Manual Target"],
            )
            self.assertIn("Single Reading", reloaded.database.enemies)
            self.assertIn("1 FF gee", reloaded.database.enemies)

    def test_item_resolution_uses_separate_database_and_exact_case_deduplication(self):
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)

            self.assertEqual(
                manager.resolve_item_name("Potion +1"),
                "Potion +1",
            )
            self.assertTrue(manager.register_item_seen("pOTION +1"))
            self.assertEqual(
                manager.resolve_item_name("pOTION +1"),
                "Potion +1",
            )

            reloaded = EntityDatabaseManager(path)
            item = reloaded.get_item("POTION +1")
            self.assertEqual(item["encounters"], 1)
            self.assertEqual(item["source"], "vision_no_hp")
            self.assertEqual(reloaded.get_item_names(), ["Potion +1"])
            self.assertEqual(reloaded.database.enemies, {})

    def test_ocr_noise_patterns_are_rejected_before_persistence(self):
        invalid_names = (
            "4m 235",
            "4m 59s",
            "12/34",
            "Lv. 20",
            "1 FF gee",
            "Bongbo @@@",
        )
        with tempfile.TemporaryDirectory() as path:
            manager = EntityDatabaseManager(path)

            for name in invalid_names:
                with self.subTest(name=name):
                    self.assertIsNone(manager.resolve_enemy_name(name))

            self.assertEqual(manager.database.enemies, {})


if __name__ == "__main__":
    unittest.main()
