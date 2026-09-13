import cv2
import numpy as np


class TemplateDetector:

    MASKED_COARSE_SCALE = 0.5
    MASKED_COARSE_MIN_AREA = 300_000
    MASKED_COARSE_THRESHOLD_MARGIN = 0.25
    MASKED_COARSE_MIN_CONFIDENCE = 0.5
    MASKED_COARSE_CANDIDATES = 5
    MASKED_REFINE_MARGIN = 16

    AUTO_SCALE_MIN = 0.45
    AUTO_SCALE_MAX = 2.0
    AUTO_SCALE_COARSE_STEP = 0.1
    AUTO_SCALE_REFINE_STEP = 0.025
    AUTO_SCALE_COARSE_FACTOR = 0.5
    AUTO_SCALE_MIN_SEARCH_AREA = 250_000
    AUTO_SCALE_THRESHOLD_MARGIN = 0.25
    AUTO_SCALE_MIN_CONFIDENCE = 0.45
    AUTO_SCALE_TOP_CANDIDATES = 3
    AUTO_SCALE_REFINE_MARGIN = 24

    @staticmethod
    def detect(image, template, scale_hint=None):
        if not TemplateDetector._valid(image, template):
            return None

        source_height, source_width = image.shape[:2]
        target_height, target_width = template.image.shape[:2]

        if (
            target_height > source_height
            or target_width > source_width
        ):
            return None

        for scale in TemplateDetector._hint_scales(scale_hint):
            detection = TemplateDetector._detect_scaled(
                image,
                template,
                scale,
            )
            if detection is not None:
                return detection

        if scale_hint is None or not TemplateDetector._same_scale(
            scale_hint,
            1.0,
        ):
            detection = TemplateDetector._detect_scaled(
                image,
                template,
                1.0,
            )
            if detection is not None:
                return detection

        if source_width * source_height < TemplateDetector.AUTO_SCALE_MIN_SEARCH_AREA:
            return None

        return TemplateDetector._detect_auto_scale(
            image,
            template,
        )

    @staticmethod
    def detect_masked(image, template, mask, grayscale=True):
        if not TemplateDetector._valid(image, template):
            return None

        if image.shape[0] * image.shape[1] >= TemplateDetector.MASKED_COARSE_MIN_AREA:
            return TemplateDetector._detect_masked_coarse(
                image,
                template,
                mask,
                grayscale,
            )

        return TemplateDetector._detect(
            image,
            template,
            cv2.TM_CCOEFF_NORMED,
            mask=mask,
            grayscale=grayscale,
        )

    @staticmethod
    def _detect_auto_scale(image, template):
        source_height, source_width = image.shape[:2]
        target_height, target_width = template.image.shape[:2]

        maximum = min(
            TemplateDetector.AUTO_SCALE_MAX,
            source_width / target_width,
            source_height / target_height,
        )

        minimum = TemplateDetector.AUTO_SCALE_MIN

        if maximum < minimum:
            return None

        factor = TemplateDetector.AUTO_SCALE_COARSE_FACTOR

        source_small = cv2.resize(
            TemplateDetector._to_gray(image),
            None,
            fx=factor,
            fy=factor,
            interpolation=cv2.INTER_AREA,
        )

        target_gray = TemplateDetector._to_gray(
            template.image
        )

        threshold = max(
            TemplateDetector.AUTO_SCALE_MIN_CONFIDENCE,
            float(template.threshold)
            - TemplateDetector.AUTO_SCALE_THRESHOLD_MARGIN,
        )

        candidates = []

        for scale in TemplateDetector._scale_range(
            minimum,
            maximum,
            TemplateDetector.AUTO_SCALE_COARSE_STEP,
        ):
            width = max(
                2,
                int(round(target_width * scale * factor)),
            )
            height = max(
                2,
                int(round(target_height * scale * factor)),
            )

            if (
                width > source_small.shape[1]
                or height > source_small.shape[0]
            ):
                continue

            target_small = cv2.resize(
                target_gray,
                (width, height),
                interpolation=(
                    cv2.INTER_AREA
                    if scale * factor < 1.0
                    else cv2.INTER_LINEAR
                ),
            )

            try:
                result = cv2.matchTemplate(
                    source_small,
                    target_small,
                    cv2.TM_CCOEFF_NORMED,
                )
            except cv2.error:
                continue

            result = TemplateDetector._sanitize(result)
            _, confidence, _, position = cv2.minMaxLoc(result)

            if confidence < threshold:
                continue

            candidates.append(
                (
                    float(confidence),
                    float(scale),
                    int(round(position[0] / factor)),
                    int(round(position[1] / factor)),
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best = None

        for _, candidate_scale, x, y in candidates[
            :TemplateDetector.AUTO_SCALE_TOP_CANDIDATES
        ]:
            scale_min = max(
                minimum,
                candidate_scale
                - TemplateDetector.AUTO_SCALE_COARSE_STEP,
            )
            scale_max = min(
                maximum,
                candidate_scale
                + TemplateDetector.AUTO_SCALE_COARSE_STEP,
            )

            estimated_width = max(
                1,
                int(round(target_width * candidate_scale)),
            )
            estimated_height = max(
                1,
                int(round(target_height * candidate_scale)),
            )

            margin = max(
                TemplateDetector.AUTO_SCALE_REFINE_MARGIN,
                estimated_width,
                estimated_height,
            )

            left = max(0, x - margin)
            top = max(0, y - margin)
            right = min(
                source_width,
                x + estimated_width + margin,
            )
            bottom = min(
                source_height,
                y + estimated_height + margin,
            )

            search_image = image[
                top:bottom,
                left:right,
            ]

            for scale in TemplateDetector._scale_range(
                scale_min,
                scale_max,
                TemplateDetector.AUTO_SCALE_REFINE_STEP,
            ):
                detection = TemplateDetector._detect_scaled(
                    search_image,
                    template,
                    scale,
                )

                if detection is None:
                    continue

                detection["x"] += left
                detection["y"] += top

                if (
                    best is None
                    or detection["confidence"]
                    > best["confidence"]
                ):
                    best = detection

        return best

    @staticmethod
    def _detect_scaled(
        image,
        template,
        scale,
        grayscale=False,
    ):
        try:
            scale = float(scale)
        except (TypeError, ValueError, OverflowError):
            return None

        if not np.isfinite(scale) or scale <= 0:
            return None

        source_height, source_width = image.shape[:2]
        original_height, original_width = template.image.shape[:2]

        width = max(
            2,
            int(round(original_width * scale)),
        )
        height = max(
            2,
            int(round(original_height * scale)),
        )

        if width > source_width or height > source_height:
            return None

        if (
            width == original_width
            and height == original_height
        ):
            target = template.image
            scale = 1.0
        else:
            target = cv2.resize(
                template.image,
                (width, height),
                interpolation=(
                    cv2.INTER_AREA
                    if scale < 1.0
                    else cv2.INTER_LINEAR
                ),
            )

        source = image

        if grayscale:
            source = TemplateDetector._to_gray(source)
            target = TemplateDetector._to_gray(target)

        try:
            result = cv2.matchTemplate(
                source,
                target,
                cv2.TM_CCOEFF_NORMED,
            )
        except cv2.error:
            return None

        result = TemplateDetector._sanitize(result)
        _, confidence, _, position = cv2.minMaxLoc(result)

        if confidence < float(template.threshold):
            return None

        return {
            "name": template.name,
            "type": template.type,
            "x": int(position[0]),
            "y": int(position[1]),
            "width": int(width),
            "height": int(height),
            "confidence": round(float(confidence), 4),
            "matched": True,
            "scale": round(float(scale), 4),
        }

    @staticmethod
    def _detect_masked_coarse(
        image,
        template,
        mask,
        grayscale=True,
    ):
        target_height, target_width = template.image.shape[:2]

        if (
            mask is None
            or mask.shape[:2] != (
                target_height,
                target_width,
            )
            or target_height > image.shape[0]
            or target_width > image.shape[1]
        ):
            return None

        source_gray = TemplateDetector._to_gray(image)
        target_gray = TemplateDetector._to_gray(template.image)
        factor = TemplateDetector.MASKED_COARSE_SCALE

        source_small = cv2.resize(
            source_gray,
            None,
            fx=factor,
            fy=factor,
            interpolation=cv2.INTER_AREA,
        )

        target_size = (
            max(1, int(round(target_width * factor))),
            max(1, int(round(target_height * factor))),
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

        mask_small = (
            mask_small > 0
        ).astype(np.uint8) * 255

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

        threshold = max(
            TemplateDetector.MASKED_COARSE_MIN_CONFIDENCE,
            float(template.threshold)
            - TemplateDetector.MASKED_COARSE_THRESHOLD_MARGIN,
        )

        for position in TemplateDetector._coarse_positions(
            result,
            target_size,
            threshold,
        ):
            x = int(round(position[0] / factor))
            y = int(round(position[1] / factor))

            margin = max(
                TemplateDetector.MASKED_REFINE_MARGIN,
                target_width // 2,
                target_height // 2,
            )

            left = max(0, x - margin)
            top = max(0, y - margin)
            right = min(
                image.shape[1],
                x + target_width + margin,
            )
            bottom = min(
                image.shape[0],
                y + target_height + margin,
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
                detection["scale"] = 1.0
                return detection

        return None

    @staticmethod
    def _detect(
        image,
        template,
        method,
        mask=None,
        grayscale=False,
    ):
        if not TemplateDetector._valid(image, template):
            return None

        source_height, source_width = image.shape[:2]
        target_height, target_width = template.image.shape[:2]

        if (
            target_height > source_height
            or target_width > source_width
        ):
            return None

        if (
            mask is not None
            and mask.shape[:2] != (
                target_height,
                target_width,
            )
        ):
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

        if confidence < float(template.threshold):
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
            "scale": 1.0,
        }

    @staticmethod
    def _hint_scales(scale_hint):
        if scale_hint is None:
            return []

        try:
            scale = float(scale_hint)
        except (TypeError, ValueError, OverflowError):
            return []

        if not np.isfinite(scale) or scale <= 0:
            return []

        values = []

        for offset in (
            0.0,
            -0.025,
            0.025,
            -0.05,
            0.05,
        ):
            candidate = min(
                TemplateDetector.AUTO_SCALE_MAX,
                max(
                    TemplateDetector.AUTO_SCALE_MIN,
                    scale + offset,
                ),
            )

            candidate = round(candidate, 4)

            if not any(
                TemplateDetector._same_scale(
                    candidate,
                    value,
                )
                for value in values
            ):
                values.append(candidate)

        return values

    @staticmethod
    def _coarse_positions(
        result,
        target_size,
        threshold,
    ):
        height, width = result.shape[:2]

        suppress_x = max(
            2,
            target_size[0] // 2,
        )
        suppress_y = max(
            2,
            target_size[1] // 2,
        )

        for _ in range(
            TemplateDetector.MASKED_COARSE_CANDIDATES
        ):
            _, confidence, _, position = cv2.minMaxLoc(result)

            if confidence < threshold:
                return

            yield position

            left = max(
                0,
                position[0] - suppress_x,
            )
            top = max(
                0,
                position[1] - suppress_y,
            )
            right = min(
                width,
                position[0] + suppress_x + 1,
            )
            bottom = min(
                height,
                position[1] + suppress_y + 1,
            )

            result[
                top:bottom,
                left:right,
            ] = -1.0

    @staticmethod
    def _scale_range(minimum, maximum, step):
        count = int(
            np.floor(
                (maximum - minimum) / step
            )
        ) + 1

        return [
            round(
                minimum + index * step,
                4,
            )
            for index in range(max(0, count))
        ]

    @staticmethod
    def _same_scale(first, second):
        try:
            return abs(
                float(first) - float(second)
            ) <= 0.0005
        except (TypeError, ValueError, OverflowError):
            return False

    @staticmethod
    def _valid(image, template):
        return bool(
            image is not None
            and template is not None
            and getattr(template, "image", None) is not None
            and hasattr(image, "shape")
            and image.ndim >= 2
        )

    @staticmethod
    def _to_gray(image):
        if image.ndim == 3:
            return cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY,
            )
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