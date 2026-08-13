import json
import math
import os
from dataclasses import asdict, dataclass


@dataclass
class MotionEstimate:
    dx_per_second: float = 0.0
    dy_per_second: float = 0.0
    confidence: float = 0.0
    samples: int = 0
    reward_per_second: float = 0.0
    contradictions: int = 0


class AdaptiveReturnPolicy:

    VERSION = 1
    KEYS = ("W", "A", "D")
    MAX_OBSERVED_SPEED = 20.0
    MIN_OBSERVED_DISTANCE = 1.25
    MIN_USABLE_CONFIDENCE = 0.12
    LOAD_CONFIDENCE_FACTOR = 0.5
    MIN_RETAINED_CONFIDENCE = 0.04
    HEADING_BIN_DEGREES = 30
    HEADING_BIN_COUNT = 12
    MIN_HEADING_SAMPLES = 3
    MIN_HEADING_CONFIDENCE = 0.35
    FALLBACK_INITIAL_CONFIDENCE = 0.08
    FALLBACK_MAX_CONFIDENCE = 0.55

    def __init__(self, storage_path=None, profile_id="default"):
        self.storage_path = storage_path
        self.profile_id = self._normalize_profile(profile_id)
        self.estimates = self._empty_estimates()
        self.heading_estimates = {}
        self.metrics = self._empty_metrics()
        self.episode_active = False
        self.dirty = False
        self._document = {"version": self.VERSION, "profiles": {}}
        self._load_document()
        self._load_profile()

    def set_profile(self, profile_id):
        profile_id = self._normalize_profile(profile_id)
        if profile_id == self.profile_id:
            return
        self.save()
        self.profile_id = profile_id
        self.estimates = self._empty_estimates()
        self.heading_estimates = {}
        self.metrics = self._empty_metrics()
        self.episode_active = False
        self.dirty = False
        self._load_profile()

    def start_episode(self):
        if self.episode_active:
            return
        self.episode_active = True
        self.metrics["episodes"] += 1
        self.dirty = True

    def finish_episode(self, success):
        if not self.episode_active:
            return
        self.episode_active = False
        key = "successful_returns" if success else "failed_returns"
        self.metrics[key] += 1
        self.dirty = True

    def cancel_episode(self):
        self.episode_active = False

    def rank_keys(
        self,
        position,
        origin,
        excluded_key=None,
        heading_deg=None,
    ):
        target = self._unit_vector(position, origin)
        ranked = []
        for index, key in enumerate(self.KEYS):
            estimate = self._estimate_for(key, heading_deg)
            projected_speed = self._dot(
                (estimate.dx_per_second, estimate.dy_per_second),
                target,
            )
            learned_score = (
                projected_speed * estimate.confidence
                if estimate.confidence >= self.MIN_USABLE_CONFIDENCE
                else 0.0
            )
            exploration = 0.2 / (estimate.samples + 1)
            score = learned_score + exploration
            if key == excluded_key:
                score -= 1000.0
            ranked.append((score, -index, key))
        ranked.sort(reverse=True)
        return [key for _, _, key in ranked]

    def observe(
        self,
        key,
        hold_ms,
        before,
        after,
        origin,
        heading_deg=None,
    ):
        if key not in self.estimates:
            return False
        try:
            duration = max(0.001, float(hold_ms) / 1000.0)
            before = (float(before[0]), float(before[1]))
            after = (float(after[0]), float(after[1]))
            origin = (float(origin[0]), float(origin[1]))
        except (TypeError, ValueError, OverflowError, IndexError):
            return False
        if not all(math.isfinite(value) for value in (*before, *after, *origin)):
            return False

        self.metrics["observations"] += 1
        delta = (after[0] - before[0], after[1] - before[1])
        travelled = math.hypot(*delta)
        speed = travelled / duration
        estimates = self._estimates_for_observation(heading_deg)
        estimate = estimates[key]
        reward = (
            math.dist(before, origin) - math.dist(after, origin)
        ) / duration

        if speed > self.MAX_OBSERVED_SPEED:
            estimate.confidence *= 0.8
            self._forget_if_unreliable(estimate)
            self.metrics["rejected_observations"] += 1
            self.dirty = True
            return False

        if travelled < self.MIN_OBSERVED_DISTANCE:
            estimate.confidence *= 0.72
            estimate.reward_per_second = self._blend(
                estimate.reward_per_second,
                min(0.0, reward),
                0.35,
            )
            self.metrics["blocked_observations"] += 1
            self._forget_if_unreliable(estimate)
            self.dirty = True
            return True

        observed = (delta[0] / duration, delta[1] / duration)
        contradiction = False
        if estimate.samples:
            expected = (estimate.dx_per_second, estimate.dy_per_second)
            contradiction = self._cosine(expected, observed) < -0.25

        if contradiction:
            alpha = 0.7
            estimate.confidence *= 0.45
            estimate.contradictions += 1
            self.metrics["contradictions"] += 1
        elif estimate.samples:
            alpha = 0.35
            estimate.confidence += (1.0 - estimate.confidence) * 0.12
        else:
            alpha = 1.0
            estimate.confidence = 0.28

        estimate.dx_per_second = self._blend(
            estimate.dx_per_second,
            observed[0],
            alpha,
        )
        estimate.dy_per_second = self._blend(
            estimate.dy_per_second,
            observed[1],
            alpha,
        )
        estimate.reward_per_second = self._blend(
            estimate.reward_per_second,
            max(-self.MAX_OBSERVED_SPEED, min(self.MAX_OBSERVED_SPEED, reward)),
            0.3,
        )
        estimate.samples += 1
        estimate.confidence = min(0.95, max(0.0, estimate.confidence))
        if estimates is not self.estimates:
            self._update_global_fallback(key, observed, reward)
        self.metrics["accepted_observations"] += 1
        self.metrics["net_improvement"] += reward * duration
        self.dirty = True
        return True

    def recommended_hold_ms(
        self,
        key,
        position,
        origin,
        arrival_distance,
        minimum_ms,
        maximum_ms,
        heading_deg=None,
    ):
        estimate = self._estimate_for(key, heading_deg)
        if estimate is None or estimate.confidence < self.MIN_USABLE_CONFIDENCE:
            return None
        target = self._unit_vector(position, origin)
        projected_speed = self._dot(
            (estimate.dx_per_second, estimate.dy_per_second),
            target,
        )
        if projected_speed <= 0.5:
            return None
        remaining = max(0.0, math.dist(position, origin) - arrival_distance)
        if remaining <= 0:
            return 0
        predicted_ms = round(remaining / projected_speed * 700.0)
        return min(maximum_ms, max(minimum_ms, predicted_ms))

    def confidence_for(self, key, heading_deg=None):
        estimate = self._estimate_for(key, heading_deg)
        return estimate.confidence if estimate is not None else 0.0

    def best_confidence(self, position, origin, heading_deg=None):
        ranking = self.rank_keys(
            position,
            origin,
            heading_deg=heading_deg,
        )
        return (
            self.confidence_for(ranking[0], heading_deg)
            if ranking
            else 0.0
        )

    def decay(self, factor=0.5):
        try:
            factor = min(1.0, max(0.0, float(factor)))
        except (TypeError, ValueError, OverflowError):
            return
        for estimate in self.estimates.values():
            estimate.confidence *= factor
            self._forget_if_unreliable(estimate)
        for estimates in self.heading_estimates.values():
            for estimate in estimates.values():
                estimate.confidence *= factor
                self._forget_if_unreliable(estimate)
        self.dirty = True

    def save(self):
        if not self.storage_path or not self.dirty:
            return False
        self._document.setdefault("profiles", {})[self.profile_id] = {
            "keys": {
                key: asdict(estimate)
                for key, estimate in self.estimates.items()
            },
            "heading_bins": {
                str(bin_index): {
                    key: asdict(estimate)
                    for key, estimate in estimates.items()
                }
                for bin_index, estimates in self.heading_estimates.items()
            },
            "metrics": dict(self.metrics),
        }
        directory = os.path.dirname(os.path.abspath(self.storage_path))
        temporary_path = f"{self.storage_path}.tmp"
        try:
            os.makedirs(directory, exist_ok=True)
            with open(temporary_path, "w", encoding="utf-8") as file:
                json.dump(
                    self._document,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )
            os.replace(temporary_path, self.storage_path)
        except (OSError, TypeError, ValueError):
            return False
        finally:
            if os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass
        self.dirty = False
        return True

    def _load_document(self):
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as file:
                document = json.load(file)
        except (OSError, ValueError, TypeError):
            return
        if (
            isinstance(document, dict)
            and document.get("version") == self.VERSION
            and isinstance(document.get("profiles"), dict)
        ):
            self._document = document

    def _load_profile(self):
        profile = self._document.get("profiles", {}).get(self.profile_id, {})
        keys = profile.get("keys", {}) if isinstance(profile, dict) else {}
        for key in self.KEYS:
            raw = keys.get(key)
            if not isinstance(raw, dict):
                continue
            try:
                estimate = MotionEstimate(
                    dx_per_second=float(raw.get("dx_per_second", 0.0)),
                    dy_per_second=float(raw.get("dy_per_second", 0.0)),
                    confidence=min(
                        0.5,
                        max(
                            0.0,
                            float(raw.get("confidence", 0.0))
                            * self.LOAD_CONFIDENCE_FACTOR,
                        ),
                    ),
                    samples=max(0, int(raw.get("samples", 0))),
                    reward_per_second=float(
                        raw.get("reward_per_second", 0.0)
                    ),
                    contradictions=max(
                        0,
                        int(raw.get("contradictions", 0)),
                    ),
                )
            except (TypeError, ValueError, OverflowError):
                continue
            values = (
                estimate.dx_per_second,
                estimate.dy_per_second,
                estimate.confidence,
                estimate.reward_per_second,
            )
            if not all(math.isfinite(value) for value in values):
                continue
            if math.hypot(
                estimate.dx_per_second,
                estimate.dy_per_second,
            ) > self.MAX_OBSERVED_SPEED:
                continue
            estimate.reward_per_second = max(
                -self.MAX_OBSERVED_SPEED,
                min(self.MAX_OBSERVED_SPEED, estimate.reward_per_second),
            )
            self.estimates[key] = estimate

        heading_bins = (
            profile.get("heading_bins", {})
            if isinstance(profile, dict)
            else {}
        )
        if isinstance(heading_bins, dict):
            for raw_index, raw_estimates in heading_bins.items():
                try:
                    bin_index = int(raw_index)
                except (TypeError, ValueError, OverflowError):
                    continue
                if (
                    not 0 <= bin_index < self.HEADING_BIN_COUNT
                    or not isinstance(raw_estimates, dict)
                ):
                    continue
                parsed = self._empty_estimates()
                loaded = False
                for key in self.KEYS:
                    estimate = self._parse_estimate(raw_estimates.get(key))
                    if estimate is not None:
                        parsed[key] = estimate
                        loaded = True
                if loaded:
                    self.heading_estimates[bin_index] = parsed

        metrics = profile.get("metrics", {}) if isinstance(profile, dict) else {}
        for key in self.metrics:
            value = metrics.get(key)
            if value is None:
                continue
            try:
                parsed = float(value) if key == "net_improvement" else int(value)
            except (TypeError, ValueError, OverflowError):
                continue
            if key == "net_improvement":
                if math.isfinite(parsed):
                    self.metrics[key] = parsed
            else:
                self.metrics[key] = max(0, parsed)

    @classmethod
    def _empty_estimates(cls):
        return {key: MotionEstimate() for key in cls.KEYS}

    def _estimate_for(self, key, heading_deg=None):
        estimate = self.estimates.get(key)
        bin_index = self._heading_bin(heading_deg)
        if bin_index is None:
            return estimate
        oriented = self.heading_estimates.get(bin_index, {}).get(key)
        if oriented is not None and self._oriented_is_usable(oriented):
            return oriented
        return estimate

    def _oriented_is_usable(self, estimate):
        coherent_samples = max(0, estimate.samples - estimate.contradictions)
        return bool(
            coherent_samples >= self.MIN_HEADING_SAMPLES
            and estimate.confidence >= self.MIN_HEADING_CONFIDENCE
        )

    def _update_global_fallback(self, key, observed, reward):
        estimate = self.estimates[key]
        limited_reward = max(
            -self.MAX_OBSERVED_SPEED,
            min(self.MAX_OBSERVED_SPEED, reward),
        )
        if not estimate.samples:
            estimate.dx_per_second = observed[0]
            estimate.dy_per_second = observed[1]
            estimate.reward_per_second = limited_reward
            estimate.confidence = self.FALLBACK_INITIAL_CONFIDENCE
            estimate.samples = 1
            return

        similarity = self._cosine(
            (estimate.dx_per_second, estimate.dy_per_second),
            observed,
        )
        if similarity < -0.25:
            alpha = 0.15
            estimate.confidence *= 0.55
            estimate.contradictions += 1
        elif similarity >= 0.5:
            alpha = 0.18
            estimate.confidence += (
                self.FALLBACK_MAX_CONFIDENCE - estimate.confidence
            ) * 0.08
        else:
            alpha = 0.08
            estimate.confidence *= 0.90

        estimate.dx_per_second = self._blend(
            estimate.dx_per_second,
            observed[0],
            alpha,
        )
        estimate.dy_per_second = self._blend(
            estimate.dy_per_second,
            observed[1],
            alpha,
        )
        estimate.reward_per_second = self._blend(
            estimate.reward_per_second,
            limited_reward,
            0.12,
        )
        estimate.samples += 1
        estimate.confidence = min(
            self.FALLBACK_MAX_CONFIDENCE,
            max(0.0, estimate.confidence),
        )
        self._forget_if_unreliable(estimate)

    def _estimates_for_observation(self, heading_deg):
        bin_index = self._heading_bin(heading_deg)
        if bin_index is None:
            return self.estimates
        return self.heading_estimates.setdefault(
            bin_index,
            self._empty_estimates(),
        )

    @classmethod
    def _heading_bin(cls, heading_deg):
        if heading_deg is None:
            return None
        try:
            heading = float(heading_deg) % 360.0
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(heading):
            return None
        return int(
            (heading + cls.HEADING_BIN_DEGREES / 2.0)
            // cls.HEADING_BIN_DEGREES
        ) % cls.HEADING_BIN_COUNT

    def _parse_estimate(self, raw):
        if not isinstance(raw, dict):
            return None
        try:
            estimate = MotionEstimate(
                dx_per_second=float(raw.get("dx_per_second", 0.0)),
                dy_per_second=float(raw.get("dy_per_second", 0.0)),
                confidence=min(
                    0.5,
                    max(
                        0.0,
                        float(raw.get("confidence", 0.0))
                        * self.LOAD_CONFIDENCE_FACTOR,
                    ),
                ),
                samples=max(0, int(raw.get("samples", 0))),
                reward_per_second=float(
                    raw.get("reward_per_second", 0.0)
                ),
                contradictions=max(
                    0,
                    int(raw.get("contradictions", 0)),
                ),
            )
        except (TypeError, ValueError, OverflowError):
            return None
        values = (
            estimate.dx_per_second,
            estimate.dy_per_second,
            estimate.confidence,
            estimate.reward_per_second,
        )
        if not all(math.isfinite(value) for value in values):
            return None
        if math.hypot(
            estimate.dx_per_second,
            estimate.dy_per_second,
        ) > self.MAX_OBSERVED_SPEED:
            return None
        estimate.reward_per_second = max(
            -self.MAX_OBSERVED_SPEED,
            min(self.MAX_OBSERVED_SPEED, estimate.reward_per_second),
        )
        return estimate

    @staticmethod
    def _empty_metrics():
        return {
            "episodes": 0,
            "successful_returns": 0,
            "failed_returns": 0,
            "observations": 0,
            "accepted_observations": 0,
            "rejected_observations": 0,
            "blocked_observations": 0,
            "contradictions": 0,
            "net_improvement": 0.0,
        }

    @staticmethod
    def _normalize_profile(profile_id):
        value = str(profile_id or "default").strip().casefold()
        return value or "default"

    @staticmethod
    def _unit_vector(position, origin):
        dx = float(origin[0]) - float(position[0])
        dy = float(origin[1]) - float(position[1])
        length = math.hypot(dx, dy)
        if length <= 0:
            return 0.0, 0.0
        return dx / length, dy / length

    @staticmethod
    def _dot(first, second):
        return first[0] * second[0] + first[1] * second[1]

    @classmethod
    def _cosine(cls, first, second):
        denominator = math.hypot(*first) * math.hypot(*second)
        if denominator <= 0:
            return 1.0
        return cls._dot(first, second) / denominator

    @staticmethod
    def _blend(previous, current, alpha):
        return previous * (1.0 - alpha) + current * alpha

    @classmethod
    def _forget_if_unreliable(cls, estimate):
        if estimate.confidence >= cls.MIN_RETAINED_CONFIDENCE:
            return
        estimate.dx_per_second = 0.0
        estimate.dy_per_second = 0.0
        estimate.confidence = 0.0
        estimate.samples = 0
        estimate.reward_per_second = 0.0
        estimate.contradictions = 0
