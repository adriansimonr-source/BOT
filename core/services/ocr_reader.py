import cv2
import pytesseract
import numpy as np

class OCRReader:

    OCR_TIMEOUT_SECONDS = 0.75

    def __init__(self):

        self.text_config = (
            "--oem 3 "
            "--psm 7"
        )

        self.number_config = (
            "--oem 3 "
            "--psm 7 "
            "-c tessedit_char_whitelist=0123456789"
        )

    def read_text(

        self,

        image

    ):

        processed = self.preprocess_text(

            image

        )

        if processed is None:

            return ""

        try:

            result = pytesseract.image_to_string(

                processed,

                config=self.text_config,

                timeout=self.OCR_TIMEOUT_SECONDS,

            )

        except RuntimeError:

            return ""

        return self.clean(

            result

        )

    def read_number(

        self,

        image

    ):

        processed = self.preprocess_number(

            image

        )

        if processed is None:

            return 0

        try:

            result = pytesseract.image_to_string(

                processed,

                config=self.number_config,

                timeout=self.OCR_TIMEOUT_SECONDS,

            )

        except RuntimeError:

            return 0

        result = self.clean(

            result

        )

        try:

            return int(result)

        except ValueError:

            return 0

    def preprocess_text(

        self,

        image

    ):

        if image is None:

            return None

        if image.size == 0:

            return None

        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )

        gray = cv2.resize(

            gray,

            None,

            fx=5,

            fy=5,

            interpolation=cv2.INTER_CUBIC

        )

        mask = cv2.inRange(

            gray,

            140,

            255

        )

        kernel = np.ones(

            (2,2),

            np.uint8

        )

        mask = cv2.morphologyEx(

            mask,

            cv2.MORPH_CLOSE,

            kernel

        )

        return mask

    def preprocess_number(

        self,

        image

    ):

        if image is None:

            return None

        if image.size == 0:

            return None

        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )

        gray = cv2.resize(

            gray,

            None,

            fx=6,

            fy=6,

            interpolation=cv2.INTER_CUBIC

        )

        _, thresh = cv2.threshold(

            gray,

            120,

            255,

            cv2.THRESH_BINARY

        )

        return thresh

    def clean(

        self,

        text

    ):

        if not text:

            return ""

        text = text.replace(

            "\n",

            " "

        )

        text = text.strip()

        return text
