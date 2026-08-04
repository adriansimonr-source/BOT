import unittest

from core.services.coordinate_reader import CoordinateReader


class CoordinateReaderTests(unittest.TestCase):

    def test_parse_text_rejects_coordinates_with_a_single_digit_axis(self):
        for text in ("1/67", "17/6", "1/6", "X 1/67 Y"):
            with self.subTest(text=text):
                self.assertIsNone(CoordinateReader.parse_text(text))

    def test_parse_text_accepts_two_and_three_digit_coordinates(self):
        self.assertEqual(
            CoordinateReader.parse_text("17/67"),
            {"x": 17, "y": 67},
        )
        self.assertEqual(
            CoordinateReader.parse_text("Pos: 123 / 456"),
            {"x": 123, "y": 456},
        )

    def test_large_jump_is_accepted_only_after_a_close_confirmation(self):
        reader = CoordinateReader()

        self.assertEqual(
            reader.validate({"x": 100, "y": 100}),
            {"x": 100, "y": 100},
        )
        self.assertIsNone(reader.validate({"x": 140, "y": 145}))
        self.assertEqual(reader.last_value, {"x": 100, "y": 100})
        self.assertEqual(reader.pending_jump, {"x": 140, "y": 145})

        confirmed = reader.validate({"x": 141, "y": 144})

        self.assertEqual(confirmed, {"x": 141, "y": 144})
        self.assertEqual(reader.last_value, confirmed)
        self.assertIsNone(reader.pending_jump)

    def test_unconfirmed_jump_is_replaced_by_the_latest_candidate(self):
        reader = CoordinateReader()
        reader.validate({"x": 100, "y": 100})

        self.assertIsNone(reader.validate({"x": 140, "y": 140}))
        self.assertIsNone(reader.validate({"x": 180, "y": 180}))

        self.assertEqual(reader.last_value, {"x": 100, "y": 100})
        self.assertEqual(reader.pending_jump, {"x": 180, "y": 180})


if __name__ == "__main__":
    unittest.main()
