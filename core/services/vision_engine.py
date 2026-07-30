import cv2
import numpy as np


from core.models.detection import Detection





class VisionEngine:



    def __init__(self):


        self.previous = None






    # =====================================
    # Procesar frame
    # =====================================


    def process(

        self,

        frame

    ):


        result = Detection()



        image = frame.image





        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )





        #
        # Primer frame
        #

        if self.previous is None:


            self.previous = gray


            return result






        #
        # Diferencia
        #

        diff = cv2.absdiff(

            self.previous,

            gray

        )



        score = np.mean(diff)





        result.score = float(score)



        result.changed = score > 5





        self.previous = gray



        return result