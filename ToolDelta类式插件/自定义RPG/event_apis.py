from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast

if TYPE_CHECKING:
    from .rpg_lib.rpg_entities import PlayerEntity, MobEntity


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

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerKillMobEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    type = BroadcastType.PLAYER_KILL_MOB


@dataclass
class MobKillPlayerEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    type = BroadcastType.MOB_KILL_PLAYER


@dataclass
class PlayerKillPlayerEvent(BaseEvent):
    killer: "PlayerEntity"
    killed: "PlayerEntity"
    type = BroadcastType.PLAYER_KILL_PLAYER
