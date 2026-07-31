import cv2
import numpy as np


from core.models.detection import Detection





class VisionEngine:


    def __init__(

        self,

        region_manager=None

    ):


        self.previous = None

        self.region_manager = region_manager






    # =====================================
    # Frame completo
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



        if self.previous is None:


            self.previous = gray

            return result





        diff = cv2.absdiff(

            self.previous,

            gray

        )



        score = np.mean(diff)



        result.score = float(score)

        result.changed = score > 5





        self.previous = gray



        return result








    # =====================================
    # Procesar región
    # =====================================

    def process_region(

        self,

        frame,

        region_name

    ):


        if self.region_manager is None:

            raise RuntimeError(

                "RegionManager no configurado"

            )





        region = self.region_manager.get(

            region_name

        )



        if region is None:

            raise ValueError(

                f"Region no existe: {region_name}"

            )





        crop = region.crop(

            frame.image

        )



        return crop