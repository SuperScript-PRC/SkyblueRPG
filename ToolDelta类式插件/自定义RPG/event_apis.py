from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast

from .rpg_lib.constants import AttackType

if TYPE_CHECKING:
    from .rpg_lib.rpg_entities import PlayerEntity, MobEntity


class BroadcastType(str, Enum):
    PLAYER_ATTACK_MOB = "rpg:PlayerAttackMob"
    MOB_ATTACK_PLAYER = "rpg:MobAttackPlayer"
    PLAYER_ATTACK_PLAYER = "rpg:PlayerAttackPlayer"
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

# TODO: 仅广播玩家直接攻击生物， 不计算效果攻击、 饰品攻击等
@dataclass
class PlayerAttackMobEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    attack_type: AttackType
    damages: list[int]
    is_crit: bool
    type = BroadcastType.PLAYER_ATTACK_MOB

@dataclass
class MobAttackPlayerEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    attack_type: AttackType
    damages: list[int]
    type = BroadcastType.MOB_ATTACK_PLAYER

@dataclass
class PlayerAttackPlayerEvent(BaseEvent):
    player: "PlayerEntity"
    target: "PlayerEntity"
    attack_type: AttackType
    damages: list[int]
    is_crit: bool
    type = BroadcastType.PLAYER_ATTACK_PLAYER

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
