import ctypes

import cv2
import numpy as np


class FrameCPUReader:

    def __init__(self):
        self.width = 0
        self.height = 0

    def set_size(self, width, height):
        self.width = int(width)
        self.height = int(height)

    def read_frame(self, mapped):
        if mapped is None or not mapped.pData:
            raise RuntimeError("Mapped no disponible")

        row_pitch = int(mapped.RowPitch)
        size = row_pitch * self.height
        memory = (ctypes.c_uint8 * size).from_address(mapped.pData)
        bgra = np.ndarray(
            shape=(self.height, self.width, 4),
            dtype=np.uint8,
            buffer=memory,
            strides=(row_pitch, 4, 1),
        )
        return cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)

    @staticmethod
    def save_png(image, filename):
        return cv2.imwrite(filename, image)
