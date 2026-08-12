from enum import Enum, auto


class TargetDecision(Enum):
    ALLOW = auto()
    REJECT = auto()


class TargetRules:
    def __init__(self):
        self.blacklist = []
        self.blacklist_enabled = False
        self.min_level = 0
        self.max_level = 999

    def set_blacklist(self, names, enabled=False):
        self.blacklist = self._normalize_names(names)
        self.blacklist_enabled = bool(enabled and self.blacklist)

    def has_filters(self):
        return self.blacklist_enabled

    def evaluate(self, target):
        if not target.exists:
            return TargetDecision.REJECT

        if not self.has_filters():
            return TargetDecision.ALLOW

        name = self._normalize_name(target.name)
        if self.blacklist_enabled and name in self.blacklist:
            return TargetDecision.REJECT

        if target.level < self.min_level or target.level > self.max_level:
            return TargetDecision.REJECT

        return TargetDecision.ALLOW

    def is_allowed(self, target):
        return self.evaluate(target) is TargetDecision.ALLOW

    @classmethod
    def _normalize_names(cls, names):
        return list(
            dict.fromkeys(
                normalized
                for name in names
                if (normalized := cls._normalize_name(name))
            )
        )

    @staticmethod
    def _normalize_name(name):
        return str(name or "").strip().casefold()
