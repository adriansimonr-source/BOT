import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class HeadingDetection:
    angle: float
    confidence: float
    observed_at: float


class MinimapHeadingDetector:

    MAX_SAMPLE_AGE_SECONDS = 0.5
    MAX_ANGLE_SPREAD_DEGREES = 24.0
    MIN_COMPONENT_AREA = 35
    MAX_COMPONENT_AREA = 500
    MIN_TIP_AREA = 3
    MAX_TIP_AREA = 56
    MAX_TIP_DIAMETER = 11
    MAX_TIP_GAP_PIXELS = 4.0
    MIN_TIP_COMPACTNESS = 0.32

    def __init__(self):
        self._samples = []

    def reset(self):
        self._samples.clear()

    def update(self, image, observed_at):
        raw = self.detect(image, observed_at)
        cutoff = float(observed_at) - self.MAX_SAMPLE_AGE_SECONDS
        self._samples = [
            sample
            for sample in self._samples
            if sample.observed_at >= cutoff
        ]
        if (
            raw is not None
            and not any(
                sample.observed_at == raw.observed_at
                for sample in self._samples
            )
        ):
            self._samples.append(raw)
            del self._samples[:-3]
        return self._filtered_detection()

    def detect(self, image, observed_at):
        if image is None or getattr(image, "size", 0) == 0:
            return None

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        red_mask = cv2.inRange(
            hsv,
            np.array((0, 80, 60), dtype=np.uint8),
            np.array((15, 255, 255), dtype=np.uint8),
        )
        red_mask |= cv2.inRange(
            hsv,
            np.array((160, 80, 60), dtype=np.uint8),
            np.array((179, 255, 255), dtype=np.uint8),
        )
        red_mask = cv2.morphologyEx(
            red_mask,
            cv2.MORPH_OPEN,
            np.ones((2, 2), dtype=np.uint8),
        )

        body = self._select_body(red_mask)
        if body is None:
            return None
        body_mask, body_center, body_area, dominance, centrality = body

        white_mask = cv2.inRange(
            hsv,
            np.array((0, 0, 120), dtype=np.uint8),
            np.array((179, 100, 255), dtype=np.uint8),
        )
        white_mask[body_mask > 0] = 0
        tip = self._select_tip(
            white_mask,
            body_mask,
            body_center,
            body_area,
        )
        if tip is None:
            return None

        tip_center, tip_area, separation = tip
        dx = tip_center[0] - body_center[0]
        dy = tip_center[1] - body_center[1]
        angle = math.degrees(math.atan2(dx, -dy)) % 360.0
        area_quality = min(1.0, body_area / 100.0)
        tip_quality = min(1.0, tip_area / 10.0)
        separation_quality = min(1.0, separation / 7.0)
        confidence = (
            0.25 * area_quality
            + 0.20 * tip_quality
            + 0.20 * separation_quality
            + 0.20 * centrality
            + 0.15 * dominance
        )
        if confidence < 0.55:
            return None
        return HeadingDetection(
            angle=angle,
            confidence=min(1.0, confidence),
            observed_at=float(observed_at),
        )

    def _select_body(self, mask):
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )
        height, width = mask.shape[:2]
        image_center = (width / 2.0, height / 2.0)
        candidates = []
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if not self.MIN_COMPONENT_AREA <= area <= self.MAX_COMPONENT_AREA:
                continue
            box_width = int(stats[label, cv2.CC_STAT_WIDTH])
            box_height = int(stats[label, cv2.CC_STAT_HEIGHT])
            if min(box_width, box_height) < 4 or max(box_width, box_height) > 38:
                continue
            aspect_ratio = max(box_width, box_height) / min(box_width, box_height)
            fill_ratio = area / float(box_width * box_height)
            if aspect_ratio > 1.8 or fill_ratio < 0.32:
                continue
            center = tuple(float(value) for value in centroids[label])
            distance = math.dist(center, image_center)
            maximum_distance = min(width, height) * 0.34
            if distance > maximum_distance:
                continue
            centrality = max(0.0, 1.0 - distance / maximum_distance)
            score = area * (0.45 + 0.55 * centrality)
            candidates.append((score, label, center, area, centrality))
        if not candidates:
            return None

        candidates.sort(reverse=True)
        score, label, center, area, centrality = candidates[0]
        second_score = candidates[1][0] if len(candidates) > 1 else 0.0
        dominance = min(1.0, score / max(1.0, second_score * 2.0))
        body_mask = np.zeros_like(mask)
        body_mask[labels == label] = 255
        return body_mask, center, area, dominance, centrality

    def _select_tip(self, mask, body_mask, body_center, body_area):
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )
        distance_from_body = cv2.distanceTransform(
            np.where(body_mask > 0, 0, 255).astype(np.uint8),
            cv2.DIST_L2,
            3,
        )
        body_radius = math.sqrt(body_area / math.pi)
        candidates = []
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if not self.MIN_TIP_AREA <= area <= self.MAX_TIP_AREA:
                continue
            width = int(stats[label, cv2.CC_STAT_WIDTH])
            height = int(stats[label, cv2.CC_STAT_HEIGHT])
            if (
                min(width, height) < 2
                or max(width, height) > self.MAX_TIP_DIAMETER
            ):
                continue
            aspect_ratio = max(width, height) / min(width, height)
            fill_ratio = area / float(width * height)
            if aspect_ratio > 2.25 or fill_ratio < 0.30:
                continue

            component_mask = np.zeros_like(mask)
            component_mask[labels == label] = 255
            contours, _ = cv2.findContours(
                component_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue
            perimeter = cv2.arcLength(max(contours, key=cv2.contourArea), True)
            compactness = (
                4.0 * math.pi * area / (perimeter * perimeter)
                if perimeter > 0.0
                else 0.0
            )
            if compactness < self.MIN_TIP_COMPACTNESS:
                continue

            center = tuple(float(value) for value in centroids[label])
            separation = math.dist(center, body_center)
            if not body_radius * 0.65 <= separation <= body_radius + 8.0:
                continue
            gap = float(np.min(distance_from_body[labels == label]))
            if gap > self.MAX_TIP_GAP_PIXELS:
                continue

            area_quality = min(1.0, area / 12.0)
            proximity = max(0.0, 1.0 - gap / self.MAX_TIP_GAP_PIXELS)
            score = (
                0.35 * min(1.0, compactness)
                + 0.25 * fill_ratio
                + 0.25 * proximity
                + 0.15 * area_quality
            )
            candidates.append((score, center, area, separation))
        if not candidates:
            return None
        _, center, area, separation = max(candidates)
        return center, area, separation

    def _filtered_detection(self):
        if len(self._samples) < 2:
            return None
        best_group = []
        for reference in self._samples:
            group = [
                sample
                for sample in self._samples
                if self._angle_distance(sample.angle, reference.angle)
                <= self.MAX_ANGLE_SPREAD_DEGREES
            ]
            if len(group) > len(best_group):
                best_group = group
        if (
            len(best_group) < 2
            or self._group_spread(best_group)
            > self.MAX_ANGLE_SPREAD_DEGREES
        ):
            return None

        sin_sum = sum(
            math.sin(math.radians(sample.angle)) * sample.confidence
            for sample in best_group
        )
        cos_sum = sum(
            math.cos(math.radians(sample.angle)) * sample.confidence
            for sample in best_group
        )
        angle = math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0
        spread = max(
            self._angle_distance(sample.angle, angle)
            for sample in best_group
        )
        confidence = (
            sum(sample.confidence for sample in best_group) / len(best_group)
        ) * max(0.0, 1.0 - spread / 45.0)
        return HeadingDetection(
            angle=angle,
            confidence=min(1.0, confidence),
            observed_at=max(sample.observed_at for sample in best_group),
        )

    @staticmethod
    def _angle_distance(first, second):
        return abs((float(first) - float(second) + 180.0) % 360.0 - 180.0)

    @classmethod
    def _group_spread(cls, samples):
        return max(
            (
                cls._angle_distance(first.angle, second.angle)
                for index, first in enumerate(samples)
                for second in samples[index + 1:]
            ),
            default=0.0,
        )
