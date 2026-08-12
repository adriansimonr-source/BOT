class HUDResolver:
    @staticmethod
    def resolve(detection, region):
        if detection is None or region is None:
            return None

        base_x = detection["x"]
        base_y = detection["y"]
        if detection.get("matched"):
            base_y += detection["height"]

        return {
            "x": base_x + region["x"],
            "y": base_y + region["y"],
            "width": region["width"],
            "height": region["height"],
        }

    @staticmethod
    def crop(image, hud):
        if image is None or hud is None:
            return None

        image_height, image_width = image.shape[:2]
        x1 = max(0, int(hud["x"]))
        y1 = max(0, int(hud["y"]))
        x2 = min(image_width, int(hud["x"] + hud["width"]))
        y2 = min(image_height, int(hud["y"] + hud["height"]))
        if x1 >= x2 or y1 >= y2:
            return None
        return image[y1:y2, x1:x2]
