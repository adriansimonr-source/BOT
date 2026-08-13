import unittest

from core.models.player_state import PlayerState


class PlayerStateTests(unittest.TestCase):

    def test_resource_timestamp_in_the_future_is_not_fresh(self):
        player = PlayerState()
        player.update_hp(25, observed_at=10.1)

        self.assertFalse(player.has_fresh_hp(now=10.0))


if __name__ == "__main__":
    unittest.main()
