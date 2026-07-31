import cv2
import numpy as np



class MinimapPositionDetector:


    def __init__(self):

        self.last_position = None



    def detect(
        self,
        image,
        minimap_region
    ):


        if image is None:

            return None


        x1 = minimap_region["x"]

        y1 = minimap_region["y"]

        x2 = x1 + minimap_region["width"]

        y2 = y1 + minimap_region["height"]



        minimap = image[
            y1:y2,
            x1:x2
        ]


        if minimap.size == 0:

            return None



        position = self.find_player_marker(
            minimap
        )


        if position is None:

            return None



        self.last_position = position


        return position





    def find_player_marker(
        self,
        minimap
    ):


        hsv = cv2.cvtColor(
            minimap,
            cv2.COLOR_BGR2HSV
        )


        # Rojo / naranja del marcador

        lower_red = np.array(
            [0,80,80]
        )


        upper_red = np.array(
            [15,255,255]
        )


        mask1 = cv2.inRange(
            hsv,
            lower_red,
            upper_red
        )


        lower_red2 = np.array(
            [160,80,80]
        )


        upper_red2 = np.array(
            [180,255,255]
        )


        mask2 = cv2.inRange(
            hsv,
            lower_red2,
            upper_red2
        )


        mask = (
            mask1 |
            mask2
        )



        contours,_ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )



        if not contours:

            return None



        biggest = max(
            contours,
            key=cv2.contourArea
        )


        area = cv2.contourArea(
            biggest
        )


        if area < 3:

            return None



        M = cv2.moments(
            biggest
        )


        if M["m00"] == 0:

            return None



        cx = int(
            M["m10"] /
            M["m00"]
        )


        cy = int(
            M["m01"] /
            M["m00"]
        )



        return {

            "x":cx,

            "y":cy,

            "confidence":min(
                area / 50,
                1.0
            )

        }