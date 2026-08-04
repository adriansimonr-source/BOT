import os
import re
import threading

import cv2
import numpy as np
import pytesseract


class CoordinateReader:

    OCR_CONFIG = (
        "--oem 3 --psm 7 "
        "-c tessedit_char_whitelist=0123456789/"
    )
    THRESHOLDS = (200, 190, 210)
    WHITE_THRESHOLDS = (200, 185)
    MAX_STEP = 20
    JUMP_CONFIRM_DISTANCE = 2

    def __init__(self, debug=False):
        self.last_value = None
        self.pending_jump = None
        self._generation = 0
        self._lock = threading.Lock()
        self.debug = debug
        if self.debug:
            os.makedirs("debug_coordinates", exist_ok=True)

    def reset(self):
        with self._lock:
            self._generation += 1
            self.last_value = None
            self.pending_jump = None

    @staticmethod
    def parse_text(text):
        normalized = str(text or "").replace(" ", "")
        match = re.search(r"(\d{2,4})/(\d{2,4})", normalized)
        if not match:
            return None

        x_text = match.group(1)[-3:]
        y_text = match.group(2)[-3:]
        x = int(x_text)
        y = int(y_text)
        if not 10 <= x <= 999 or not 10 <= y <= 999:
            return None
        return {"x": x, "y": y}

    def validate(self, coord):
        with self._lock:
            return self._validate_locked(coord)

    def _validate_locked(self, coord):
        if self.last_value is None:
            self.last_value = coord
            self.pending_jump = None
            return coord

        dx = abs(coord["x"] - self.last_value["x"])
        dy = abs(coord["y"] - self.last_value["y"])
        if dx <= self.MAX_STEP and dy <= self.MAX_STEP:
            self.last_value = coord
            self.pending_jump = None
            return coord

        if self.pending_jump is not None:
            pending_dx = abs(coord["x"] - self.pending_jump["x"])
            pending_dy = abs(coord["y"] - self.pending_jump["y"])
            if (
                pending_dx <= self.JUMP_CONFIRM_DISTANCE
                and pending_dy <= self.JUMP_CONFIRM_DISTANCE
            ):
                self.last_value = coord
                self.pending_jump = None
                return coord

        self.pending_jump = coord
        return None

    def read(self, image):
        if image is None or image.size == 0:
            return None

        with self._lock:
            generation = self._generation

        self._save("full_coordinate.png", image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self._save("coordinate_gray.png", gray)

        masks = []
        for threshold in self.WHITE_THRESHOLDS:
            # Exigir brillo en B, G y R elimina iconos de colores sin borrar texto blanco.
            mask = cv2.inRange(
                image,
                np.array((threshold, threshold, threshold), dtype=np.uint8),
                np.array((255, 255, 255), dtype=np.uint8),
            )
            masks.append((f"white_{threshold}", mask))

        for threshold in self.THRESHOLDS:
            _, mask = cv2.threshold(
                gray,
                threshold,
                255,
                cv2.THRESH_BINARY,
            )
            masks.append((f"gray_{threshold}", mask))

        for name, mask in masks:
            self._save(f"coordinate_{name}.png", mask)
            text = pytesseract.image_to_string(mask, config=self.OCR_CONFIG)
            coord = self.parse_text(text)
            if coord is not None:
                with self._lock:
                    if generation != self._generation:
                        return None
                    return self._validate_locked(coord)
        return None

    def _save(self, filename, image):
        if self.debug:
            cv2.imwrite(os.path.join("debug_coordinates", filename), image)
