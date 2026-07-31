import cv2
import numpy as np



class TargetValidator:



    def __init__(self):

        pass





    # =====================================
    # Validar enemigo
    # =====================================


    def validate_enemy(

        self,

        hud_image

    ):


        if hud_image is None:

            return False



        # comprobar que existe HP roja

        has_hp = self.has_red_bar(

            hud_image

        )


        if not has_hp:

            return False





        # comprobar si existe MP azul

        has_mp = self.has_blue_bar(

            hud_image

        )


        # Si tiene azul es jugador

        if has_mp:

            return False



        return True





    # =====================================
    # Barra roja
    # =====================================


    def has_red_bar(

        self,

        image

    ):


        hsv = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2HSV

        )



        lower1 = np.array(

            [0,80,80]

        )


        upper1 = np.array(

            [10,255,255]

        )


        lower2 = np.array(

            [170,80,80]

        )


        upper2 = np.array(

            [180,255,255]

        )



        mask1 = cv2.inRange(

            hsv,

            lower1,

            upper1

        )


        mask2 = cv2.inRange(

            hsv,

            lower2,

            upper2

        )



        mask = mask1 | mask2



        pixels = cv2.countNonZero(

            mask

        )



        return pixels > 100





    # =====================================
    # Barra azul
    # =====================================


    def has_blue_bar(

        self,

        image

    ):


        hsv = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2HSV

        )



        lower = np.array(

            [90,60,50]

        )


        upper = np.array(

            [140,255,255]

        )



        mask = cv2.inRange(

            hsv,

            lower,

            upper

        )



        pixels = cv2.countNonZero(

            mask

        )



        return pixels > 100