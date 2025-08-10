from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rpg_entities import PlayerEntity, MobEntity


class BroadcastType(str, Enum):
    PLAYER_KILL_MOB = "rpg:PlayerKillMob"
    MOB_KILL_PLAYER = "rpg:MobKillPlayer"
    PLAYER_KILL_PLAYER = "rpg:PlayerKillPlayer"
    PLAYER_SET_SKILL = "rpg:PlayerSetSkill"
    PLAYER_USE_SKILL = "rpg:PlayerUseSkill"
    PLAYER_SET_ULT = "rpg:PlayerSetUlt"
    PLAYER_USE_ULT = "rpg:PlayerUseUlt"


class BaseEvent:
    type: BroadcastType


@dataclass
class PlayerKillMobEvent:
    player: "PlayerEntity"
    mob: "MobEntity"
    type = BroadcastType.PLAYER_KILL_MOB


@dataclass
class MobKillPlayerEvent:
    player: "PlayerEntity"
    mob: "MobEntity"
    type = BroadcastType.MOB_KILL_PLAYER


@dataclass
class PlayerKillPlayerEvent:
    killer: "PlayerEntity"
    killed: "PlayerEntity"
    type = BroadcastType.PLAYER_KILL_PLAYER
