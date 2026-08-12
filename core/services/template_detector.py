import cv2


class TemplateDetector:
    @staticmethod
    def detect(image, template):
        if image is None or template is None or template.image is None:
            return None

        source_height, source_width = image.shape[:2]
        target_height, target_width = template.image.shape[:2]
        if target_height > source_height or target_width > source_width:
            return None

        result = cv2.matchTemplate(
            image,
            template.image,
            cv2.TM_CCOEFF_NORMED,
        )
        _, confidence, _, position = cv2.minMaxLoc(result)
        if confidence < template.threshold:
            return None

        return {
            "name": template.name,
            "type": template.type,
            "x": int(position[0]),
            "y": int(position[1]),
            "width": int(target_width),
            "height": int(target_height),
            "confidence": round(float(confidence), 4),
            "matched": True,
        }
