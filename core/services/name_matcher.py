from core.services.ocr_reader import OCRReader


class NameMatcher:
    def __init__(self):
        self.ocr = OCRReader()

    def read_enemy_name(self, image):
        return self.normalize(self.ocr.read_text(image))

    def read_number(self, image):
        try:
            return int(self.ocr.read_number(image))
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def normalize(text):
        if not text:
            return ""
        text = str(text).replace("\n", " ")
        for character in ("|", "_", "—", "–", "~", "`", '"'):
            text = text.replace(character, "")
        text = " ".join(text.split()).strip()
        return text if len(text) >= 2 else ""
