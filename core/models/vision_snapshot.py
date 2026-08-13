from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlayerVisionSnapshot:
    hp_percent: float
    hp_valid: bool
    hp_updated_at: float
    mp_percent: float
    mp_valid: bool
    mp_updated_at: float
    x: int
    y: int
    z: int
    position_valid: bool
    position_updated_at: float
    position_revision: int
    position_history: tuple
    minimap_heading_deg: float | None
    minimap_heading_confidence: float
    minimap_heading_valid: bool
    minimap_heading_updated_at: float
    minimap_heading_revision: int


@dataclass(frozen=True, slots=True)
class TargetVisionSnapshot:
    selection_id: int
    exists: bool
    name: str
    level: int
    hp_percent: float
    hp_valid: bool
    hp_observed_at: float | None
    visible: bool
    targetable: bool
    identity_pending: bool
    auto_target_decision: object
    auto_target_decision_selection_id: int | None


@dataclass(frozen=True, slots=True)
class VisionSnapshot:
    sequence: int
    published_at: float
    frame_observed_at: float
    connected: bool
    position_epoch: int
    player: PlayerVisionSnapshot
    target: TargetVisionSnapshot
    in_combat: bool

    @classmethod
    def from_state(
        cls,
        state,
        sequence,
        published_at,
        frame_observed_at,
        position_epoch,
    ):
        player = state.player
        target = state.target
        return cls(
            sequence=int(sequence),
            published_at=float(published_at),
            frame_observed_at=float(frame_observed_at or 0.0),
            connected=bool(state.connected),
            position_epoch=int(position_epoch),
            player=PlayerVisionSnapshot(
                hp_percent=float(player.hp_percent),
                hp_valid=bool(player.hp_valid),
                hp_updated_at=float(player.hp_updated_at),
                mp_percent=float(player.mp_percent),
                mp_valid=bool(player.mp_valid),
                mp_updated_at=float(player.mp_updated_at),
                x=int(player.x),
                y=int(player.y),
                z=int(player.z),
                position_valid=bool(player.position_valid),
                position_updated_at=float(player.position_updated_at),
                position_revision=int(player.position_revision),
                position_history=tuple(player.position_history),
                minimap_heading_deg=player.minimap_heading_deg,
                minimap_heading_confidence=float(
                    player.minimap_heading_confidence
                ),
                minimap_heading_valid=bool(player.minimap_heading_valid),
                minimap_heading_updated_at=float(
                    player.minimap_heading_updated_at
                ),
                minimap_heading_revision=int(
                    player.minimap_heading_revision
                ),
            ),
            target=TargetVisionSnapshot(
                selection_id=int(target.selection_id),
                exists=bool(target.exists),
                name=str(target.name),
                level=int(target.level),
                hp_percent=float(target.hp_percent),
                hp_valid=bool(target.hp_valid),
                hp_observed_at=target.hp_observed_at,
                visible=bool(target.visible),
                targetable=bool(target.targetable),
                identity_pending=bool(target.identity_pending),
                auto_target_decision=target.auto_target_decision,
                auto_target_decision_selection_id=(
                    target.auto_target_decision_selection_id
                ),
            ),
            in_combat=bool(state.in_combat),
        )
