import cv2
import numpy as np


class TemplateDetector:

    MASKED_COARSE_SCALE = 0.5
    MASKED_COARSE_MIN_AREA = 300_000
    MASKED_COARSE_THRESHOLD_MARGIN = 0.25
    MASKED_COARSE_MIN_CONFIDENCE = 0.5
    MASKED_COARSE_CANDIDATES = 5
    MASKED_REFINE_MARGIN = 16

    @staticmethod
    def detect(image, template):
        return TemplateDetector._detect(
            image,
            template,
            cv2.TM_CCOEFF_NORMED,
        )

    @staticmethod
    def detect_masked(image, template, mask, grayscale=True):
        if image is None or template is None or template.image is None:
            return None
        if (
            image.shape[0] * image.shape[1]
            >= TemplateDetector.MASKED_COARSE_MIN_AREA
        ):
            return TemplateDetector._detect_masked_coarse(
                image,
                template,
                mask,
                grayscale,
            )
        detection = TemplateDetector._detect(
            image,
            template,
            cv2.TM_CCOEFF_NORMED,
            mask=mask,
            grayscale=grayscale,
        )
        return detection

    @staticmethod
    def _detect_masked_coarse(
        image,
        template,
        mask,
        grayscale=True,
    ):
        target_height, target_width = template.image.shape[:2]
        if mask is None or mask.shape[:2] != (target_height, target_width):
            return None
        if target_height > image.shape[0] or target_width > image.shape[1]:
            return None

        source_gray = TemplateDetector._to_gray(image)
        target_gray = TemplateDetector._to_gray(template.image)
        scale = TemplateDetector.MASKED_COARSE_SCALE
        source_small = cv2.resize(
            source_gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )
        target_size = (
            max(1, int(round(target_width * scale))),
            max(1, int(round(target_height * scale))),
        )
        target_small = cv2.resize(
            target_gray,
            target_size,
            interpolation=cv2.INTER_AREA,
        )
        mask_small = cv2.resize(
            mask,
            target_size,
            interpolation=cv2.INTER_NEAREST,
        )
        mask_small = (mask_small > 0).astype(np.uint8) * 255
        try:
            result = cv2.matchTemplate(
                source_small,
                target_small,
                cv2.TM_CCOEFF_NORMED,
                mask=mask_small,
            )
        except cv2.error:
            return None
        result = TemplateDetector._sanitize(result)
        coarse_threshold = max(
            TemplateDetector.MASKED_COARSE_MIN_CONFIDENCE,
            float(template.threshold)
            - TemplateDetector.MASKED_COARSE_THRESHOLD_MARGIN,
        )
        for position in TemplateDetector._coarse_positions(
            result,
            target_size,
            coarse_threshold,
        ):
            estimated_x = int(round(position[0] / scale))
            estimated_y = int(round(position[1] / scale))
            margin = max(
                TemplateDetector.MASKED_REFINE_MARGIN,
                target_width // 2,
                target_height // 2,
            )
            left = max(0, estimated_x - margin)
            top = max(0, estimated_y - margin)
            right = min(
                image.shape[1],
                estimated_x + target_width + margin,
            )
            bottom = min(
                image.shape[0],
                estimated_y + target_height + margin,
            )
            detection = TemplateDetector._detect(
                image[top:bottom, left:right],
                template,
                cv2.TM_CCOEFF_NORMED,
                mask=mask,
                grayscale=grayscale,
            )
            if detection is not None:
                detection["x"] += left
                detection["y"] += top
                return detection
        return None

    @staticmethod
    def _coarse_positions(result, target_size, threshold):
        height, width = result.shape[:2]
        suppress_x = max(2, target_size[0] // 2)
        suppress_y = max(2, target_size[1] // 2)
        for _ in range(TemplateDetector.MASKED_COARSE_CANDIDATES):
            _, confidence, _, position = cv2.minMaxLoc(result)
            if confidence < threshold:
                return
            yield position
            left = max(0, position[0] - suppress_x)
            top = max(0, position[1] - suppress_y)
            right = min(width, position[0] + suppress_x + 1)
            bottom = min(height, position[1] + suppress_y + 1)
            result[top:bottom, left:right] = -1.0

    @staticmethod
    def _detect(image, template, method, mask=None, grayscale=False):
        if image is None or template is None or template.image is None:
            return None

        source_height, source_width = image.shape[:2]
        target_height, target_width = template.image.shape[:2]
        if target_height > source_height or target_width > source_width:
            return None
        if mask is not None and mask.shape[:2] != (target_height, target_width):
            return None

        source = image
        target = template.image
        if grayscale:
            source = TemplateDetector._to_gray(source)
            target = TemplateDetector._to_gray(target)

        try:
            result = cv2.matchTemplate(
                source,
                target,
                method,
                mask=mask,
            )
        except cv2.error:
            return None
        result = TemplateDetector._sanitize(result)
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

    @staticmethod
    def _to_gray(image):
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def _sanitize(result):
        return np.nan_to_num(
            result,
            copy=False,
            nan=-1.0,
            posinf=-1.0,
            neginf=-1.0,
        )
