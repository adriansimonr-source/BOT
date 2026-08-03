class HUDResolver:



    def resolve(
        self,
        detection,
        region
    ):


        if detection is None:

            return None



        # =====================================
        # Si viene de un anchor detectado
        # =====================================


        if "matched" in detection:


            base_x = detection["x"]

            base_y = (
                detection["y"]
                +
                detection["height"]
            )



        # =====================================
        # Si viene de otra region resuelta
        # =====================================


        else:


            base_x = detection["x"]

            base_y = detection["y"]





        return {


            "x": base_x + region["x"],


            "y": base_y + region["y"],


            "width": region["width"],


            "height": region["height"]

        }





    def crop(
        self,
        image,
        hud
    ):


        x = hud["x"]

        y = hud["y"]

        w = hud["width"]

        h = hud["height"]



        return image[

            y:y+h,

            x:x+w

        ]