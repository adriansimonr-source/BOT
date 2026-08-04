from enum import Enum, auto


class TargetDecision(Enum):

    ALLOW = auto()
    PENDING = auto()
    REJECT = auto()


class TargetRules:

    def __init__(self):
        self.blacklist = []
        self.unique_targets = []
        self.unique_targets_enabled = False
        self.min_level = 0
        self.max_level = 999
        self.allow_unknown = True

    def set_blacklist(self, names):
        self.blacklist = self._normalize_names(names)

    def set_unique_targets(self, names, enabled=False):
        self.unique_targets = self._normalize_names(names)
        self.unique_targets_enabled = bool(enabled and self.unique_targets)

    def add_blacklist(self, name):
        normalized = self._normalize_name(name)
        if normalized and normalized not in self.blacklist:
            self.blacklist.append(normalized)

    def remove_blacklist(self, name):
        normalized = self._normalize_name(name)
        if normalized in self.blacklist:
            self.blacklist.remove(normalized)

    def evaluate(self, target):
        if not target.exists:
            return TargetDecision.REJECT

        name = self._normalize_name(target.name)
        if not name:
            if self.allow_unknown and not self.unique_targets_enabled:
                return TargetDecision.ALLOW
            return TargetDecision.PENDING

        if name in self.blacklist:
            return TargetDecision.REJECT

        if self.unique_targets_enabled and name not in self.unique_targets:
            return TargetDecision.REJECT

        if target.level < self.min_level or target.level > self.max_level:
            return TargetDecision.REJECT

        return TargetDecision.ALLOW

    def is_allowed(self, target):
        return self.evaluate(target) is TargetDecision.ALLOW

    @classmethod
    def _normalize_names(cls, names):
        return list(dict.fromkeys(
            normalized
            for name in names
            if (normalized := cls._normalize_name(name))
        ))

    @staticmethod
    def _normalize_name(name):
        return str(name or "").strip().casefold()
