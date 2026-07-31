import cv2
import numpy as np





class TemplateDetector:



    def __init__(self):

        pass





    # =====================================
    # DETECCION NORMAL
    # Devuelve mejor resultado
    # =====================================


    def detect(

        self,

        image,

        template

    ):


        results = self.detect_all(

            image,

            template

        )



        if not results:

            return None



        # devolver el mejor

        return results[0]







    # =====================================
    # DETECCION MULTIPLE
    # Devuelve todos los matches
    # =====================================


    def detect_all(

        self,

        image,

        template

    ):


        if template is None:

            return []



        if template.image is None:

            return []





        source = image


        target = template.image





        result = cv2.matchTemplate(

            source,

            target,

            cv2.TM_CCOEFF_NORMED

        )



        locations = np.where(

            result >= template.threshold

        )



        detections = []



        h, w = target.shape[:2]



        for y, x in zip(

            locations[0],

            locations[1]

        ):



            confidence = float(

                result[y, x]

            )



            detections.append(


                {

                    "name": template.name,


                    "type": template.type,


                    "x": int(x),


                    "y": int(y),


                    "width": int(w),


                    "height": int(h),


                    "confidence": round(

                        confidence,

                        4

                    ),


                    "matched": True

                }

            )







        # eliminar duplicados cercanos

        detections = self.remove_duplicates(

            detections

        )





        # ordenar por confianza

        detections.sort(

            key=lambda x: x["confidence"],

            reverse=True

        )



        return detections








    # =====================================
    # QUITAR REPETIDOS
    # =====================================


    def remove_duplicates(

        self,

        detections,

        distance=20

    ):


        filtered = []



        for item in detections:



            duplicate = False



            for saved in filtered:



                dx = abs(

                    item["x"]

                    -

                    saved["x"]

                )


                dy = abs(

                    item["y"]

                    -

                    saved["y"]

                )



                if dx < distance and dy < distance:


                    duplicate = True

                    break




            if not duplicate:


                filtered.append(

                    item

                )



        return filtered