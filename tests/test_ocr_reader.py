import unittest
from unittest.mock import patch

import numpy as np

from core.services.ocr_reader import OCRReader


class OCRReaderTests(unittest.TestCase):

    def setUp(self):
        self.reader = OCRReader()
        self.image = np.zeros((4, 12, 3), dtype=np.uint8)

    def test_text_timeout_returns_empty_text(self):
        with patch(
            "core.services.ocr_reader.pytesseract.image_to_string",
            side_effect=RuntimeError("timeout"),
        ) as image_to_string:
            result = self.reader.read_text(self.image)

        self.assertEqual(result, "")
        self.assertEqual(
            image_to_string.call_args.kwargs["timeout"],
            self.reader.OCR_TIMEOUT_SECONDS,
        )

    def test_number_timeout_returns_zero(self):
        with patch(
            "core.services.ocr_reader.pytesseract.image_to_string",
            side_effect=RuntimeError("timeout"),
        ) as image_to_string:
            result = self.reader.read_number(self.image)

        self.assertEqual(result, 0)
        self.assertEqual(
            image_to_string.call_args.kwargs["timeout"],
            self.reader.OCR_TIMEOUT_SECONDS,
        )


if __name__ == "__main__":
    unittest.main()
