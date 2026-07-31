class HUDResolver:


    def resolve(self, detection, region):


        if detection is None:
            return None



        anchor_bottom_y = (
            detection["y"] +
            detection["height"]
        )



        return {


            "x": detection["x"] + region["x"],


            "y": anchor_bottom_y + region["y"],


            "width": region["width"],


            "height": region["height"]

        }



    def crop(self, image, hud):


        x = hud["x"]
        y = hud["y"]

        w = hud["width"]
        h = hud["height"]


        return image[
            y:y+h,
            x:x+w
        ]