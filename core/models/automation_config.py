from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionConfig:
    enabled: bool
    key_value: str
    interval_ms: int

    def is_enabled(self):
        return self.enabled

    def key(self):
        return self.key_value

    def interval(self):
        return self.interval_ms


@dataclass(frozen=True, slots=True)
class ResourceConfig(ActionConfig):
    threshold_percent: int

    def threshold(self):
        return self.threshold_percent


@dataclass(frozen=True, slots=True)
class SkillConfigValue:
    enabled: bool
    key_value: str
    interval_ms: int

    def is_enabled(self):
        return self.enabled

    def skill_number(self):
        return self.key_value

    def time(self):
        return self.interval_ms


@dataclass(frozen=True, slots=True)
class AutomationConfig:
    revision: int = 0
    auto_target: ActionConfig | None = None
    auto_attack: ActionConfig | None = None
    auto_loot: ActionConfig | None = None
    auto_pot1: ResourceConfig | None = None
    auto_mp: ResourceConfig | None = None
    auto_heal: ResourceConfig | None = None
    skills: tuple[SkillConfigValue, ...] | None = None
    ignored_targets: tuple[str, ...] = ()
    ignore_enabled: bool = False
    bot_mode: object | None = None
    quiet_seconds: int | None = None


def config_from_widgets(
    right_panel,
    center_panel=None,
    character_group=None,
    revision=0,
):
    ignored_targets = tuple(
        str(name).strip()
        for name in right_panel.get_ignored_targets()
        if str(name).strip()
    )
    ignore_checkbox = getattr(right_panel, "ignore_targets", None)
    ignore_enabled = bool(
        ignore_checkbox is not None
        and ignore_checkbox.isChecked()
        and ignored_targets
    )

    return AutomationConfig(
        revision=max(0, int(revision)),
        auto_target=_action_from_panel(right_panel, "auto_target"),
        auto_attack=_action_from_panel(right_panel, "auto_attack"),
        auto_loot=_action_from_panel(right_panel, "auto_loot"),
        auto_pot1=_resource_from_panel(right_panel, "auto_pot1"),
        auto_mp=_resource_from_panel(right_panel, "auto_mp"),
        auto_heal=_resource_from_panel(right_panel, "auto_heal"),
        skills=(
            tuple(
                SkillConfigValue(
                    bool(card.is_enabled()),
                    str(card.skill_number()),
                    max(1, int(card.time())),
                )
                for card in center_panel.skills
            )
            if center_panel is not None
            else None
        ),
        ignored_targets=ignored_targets,
        ignore_enabled=ignore_enabled,
        bot_mode=(
            character_group.get_bot_mode()
            if character_group is not None
            else None
        ),
        quiet_seconds=(
            int(character_group.get_quiet_seconds())
            if character_group is not None
            else None
        ),
    )


def _action_from_panel(panel, name):
    card = getattr(panel, name, None)
    if card is None:
        return None
    return ActionConfig(
        bool(card.is_enabled()),
        str(card.key()),
        max(1, int(card.interval())),
    )


def _resource_from_panel(panel, name):
    card = getattr(panel, name, None)
    if card is None:
        return None
    return ResourceConfig(
        bool(card.is_enabled()),
        str(card.key()),
        max(1, int(card.interval())),
        max(0, min(100, int(card.threshold()))),
    )
