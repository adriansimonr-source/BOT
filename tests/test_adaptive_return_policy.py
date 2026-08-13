import json
import os
import tempfile
import unittest
from unittest.mock import patch

from core.modules.adaptive_return_policy import AdaptiveReturnPolicy


class AdaptiveReturnPolicyTests(unittest.TestCase):

    def test_heading_bins_keep_different_camera_directions_independent(self):
        policy = AdaptiveReturnPolicy()
        position = (110, 100)
        origin = (100, 100)

        for _ in range(3):
            policy.observe(
                "W",
                1000,
                position,
                (105, 100),
                origin,
                heading_deg=0,
            )
            policy.observe(
                "D",
                1000,
                position,
                (105, 100),
                origin,
                heading_deg=90,
            )

        self.assertEqual(
            policy.rank_keys(position, origin, heading_deg=0)[0],
            "W",
        )
        self.assertEqual(
            policy.rank_keys(position, origin, heading_deg=90)[0],
            "D",
        )

    def test_heading_bin_needs_three_coherent_observations_to_govern(self):
        policy = AdaptiveReturnPolicy()
        position = (110, 100)
        origin = (100, 100)
        for _ in range(2):
            policy.observe("A", 1000, position, (105, 100), origin)
            policy.observe(
                "W",
                1000,
                position,
                (105, 100),
                origin,
                heading_deg=0,
            )

        self.assertEqual(
            policy.rank_keys(position, origin, heading_deg=0)[0],
            "A",
        )

        policy.observe(
            "W",
            1000,
            position,
            (105, 100),
            origin,
            heading_deg=0,
        )

        self.assertEqual(
            policy.rank_keys(position, origin, heading_deg=0)[0],
            "W",
        )

    def test_contradiction_does_not_complete_heading_warmup(self):
        policy = AdaptiveReturnPolicy()
        position = (110, 100)
        origin = (100, 100)
        for _ in range(3):
            policy.observe("A", 1000, position, (105, 100), origin)
        for _ in range(2):
            policy.observe(
                "W",
                1000,
                position,
                (105, 100),
                origin,
                heading_deg=0,
            )
        policy.observe(
            "W",
            1000,
            (105, 100),
            (110, 100),
            origin,
            heading_deg=0,
        )

        oriented = policy.heading_estimates[0]["W"]
        self.assertEqual(oriented.samples, 3)
        self.assertEqual(oriented.contradictions, 1)
        self.assertEqual(
            policy.rank_keys(position, origin, heading_deg=0)[0],
            "A",
        )

    def test_heading_learning_updates_global_fallback_conservatively(self):
        policy = AdaptiveReturnPolicy()
        position = (110, 100)
        origin = (100, 100)

        policy.observe(
            "D",
            1000,
            position,
            (105, 100),
            origin,
            heading_deg=90,
        )

        fallback = policy.estimates["D"]
        self.assertEqual(fallback.samples, 1)
        self.assertEqual(fallback.dx_per_second, -5.0)
        self.assertLess(
            fallback.confidence,
            policy.MIN_USABLE_CONFIDENCE,
        )

        for _ in range(2):
            policy.observe(
                "D",
                1000,
                position,
                (105, 100),
                origin,
                heading_deg=90,
            )

        self.assertEqual(fallback.samples, 3)
        self.assertGreaterEqual(
            fallback.confidence,
            policy.MIN_USABLE_CONFIDENCE,
        )

    def test_forgetting_clears_observation_history(self):
        policy = AdaptiveReturnPolicy()
        estimate = policy.estimates["W"]
        estimate.dx_per_second = -5.0
        estimate.dy_per_second = 1.0
        estimate.confidence = 0.05
        estimate.samples = 7
        estimate.reward_per_second = 2.0
        estimate.contradictions = 3

        policy.decay(0.5)

        self.assertEqual(estimate.dx_per_second, 0.0)
        self.assertEqual(estimate.dy_per_second, 0.0)
        self.assertEqual(estimate.confidence, 0.0)
        self.assertEqual(estimate.samples, 0)
        self.assertEqual(estimate.reward_per_second, 0.0)
        self.assertEqual(estimate.contradictions, 0)

    def test_learning_ranks_the_key_that_moves_toward_the_origin(self):
        policy = AdaptiveReturnPolicy()
        origin = (100, 100)

        self.assertEqual(
            policy.rank_keys((120, 100), origin),
            ["W", "A", "D"],
        )
        self.assertTrue(
            policy.observe(
                "A",
                400,
                (120, 100),
                (117, 100),
                origin,
            )
        )

        self.assertEqual(
            policy.rank_keys((120, 100), origin)[0],
            "A",
        )
        self.assertGreater(policy.confidence_for("A"), 0.0)

    def test_contradiction_replaces_a_stale_direction_model(self):
        policy = AdaptiveReturnPolicy()
        origin = (100, 100)
        policy.observe("W", 400, (120, 100), (118, 100), origin)

        policy.observe("W", 400, (118, 100), (120, 100), origin)

        self.assertEqual(policy.estimates["W"].contradictions, 1)
        self.assertNotEqual(
            policy.rank_keys((120, 100), origin)[0],
            "W",
        )

    def test_impossible_coordinate_jump_is_rejected(self):
        policy = AdaptiveReturnPolicy()

        self.assertFalse(
            policy.observe(
                "W",
                250,
                (100, 100),
                (200, 200),
                (90, 90),
            )
        )
        self.assertEqual(policy.estimates["W"].samples, 0)
        self.assertEqual(policy.metrics["rejected_observations"], 1)

    def test_one_coordinate_of_jitter_does_not_create_a_motion_vector(self):
        policy = AdaptiveReturnPolicy()

        self.assertTrue(
            policy.observe(
                "W",
                400,
                (120, 100),
                (119, 100),
                (100, 100),
            )
        )

        self.assertEqual(policy.estimates["W"].samples, 0)
        self.assertEqual(policy.confidence_for("W"), 0.0)

    def test_vector_below_usable_confidence_cannot_dominate_ranking(self):
        policy = AdaptiveReturnPolicy()
        estimate = policy.estimates["W"]
        estimate.dx_per_second = -20.0
        estimate.confidence = policy.MIN_USABLE_CONFIDENCE - 0.01
        estimate.samples = 10

        self.assertNotEqual(
            policy.rank_keys((120, 100), (100, 100))[0],
            "W",
        )

    def test_learned_speed_adapts_the_hold_without_exceeding_limits(self):
        policy = AdaptiveReturnPolicy()
        origin = (100, 100)
        policy.observe("W", 400, (120, 100), (118, 100), origin)

        hold_ms = policy.recommended_hold_ms(
            "W",
            (105, 100),
            origin,
            arrival_distance=2,
            minimum_ms=250,
            maximum_ms=650,
        )

        self.assertEqual(hold_ms, 420)

    def test_learning_persists_per_game_with_lower_startup_confidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "navigation.json")
            policy = AdaptiveReturnPolicy(path, "Kathana")
            policy.start_episode()
            policy.observe(
                "D",
                400,
                (120, 100),
                (117, 100),
                (100, 100),
            )
            original_confidence = policy.confidence_for("D")
            policy.finish_episode(success=True)

            self.assertTrue(policy.save())

            restored = AdaptiveReturnPolicy(path, "kathana")
            self.assertEqual(
                restored.rank_keys((120, 100), (100, 100))[0],
                "D",
            )
            self.assertGreater(restored.confidence_for("D"), 0.0)
            self.assertLess(
                restored.confidence_for("D"),
                original_confidence,
            )
            self.assertEqual(restored.metrics["successful_returns"], 1)

            restored.set_profile("another-game")
            self.assertEqual(restored.estimates["D"].samples, 0)

    def test_invalid_persisted_data_falls_back_to_an_empty_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "navigation.json")
            with open(path, "w", encoding="utf-8") as file:
                json.dump({"version": 999, "profiles": []}, file)

            policy = AdaptiveReturnPolicy(path, "kathana")

            self.assertTrue(
                all(
                    estimate.samples == 0
                    for estimate in policy.estimates.values()
                )
            )

    def test_unsafe_persisted_vectors_and_metrics_are_discarded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "navigation.json")
            document = {
                "version": 1,
                "profiles": {
                    "kathana": {
                        "keys": {
                            "W": {
                                "dx_per_second": 1e100,
                                "dy_per_second": 0,
                                "confidence": 1,
                                "samples": 100,
                            }
                        },
                        "metrics": {"net_improvement": float("nan")},
                    }
                },
            }
            with open(path, "w", encoding="utf-8") as file:
                json.dump(document, file)

            policy = AdaptiveReturnPolicy(path, "kathana")

            self.assertEqual(policy.estimates["W"].samples, 0)
            self.assertEqual(policy.metrics["net_improvement"], 0.0)

    def test_optional_persistence_failure_never_breaks_navigation(self):
        policy = AdaptiveReturnPolicy("unavailable/navigation.json")
        policy.start_episode()

        with patch(
            "core.modules.adaptive_return_policy.os.makedirs",
            side_effect=OSError("read only"),
        ):
            self.assertFalse(policy.save())

        self.assertTrue(policy.dirty)


if __name__ == "__main__":
    unittest.main()
