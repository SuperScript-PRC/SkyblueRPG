from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

from .rpg_lib.constants import AttackData

if TYPE_CHECKING:
    from . import SlotItem
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
    MOB_INITED = "rpg:MobInited"
    PLAYER_DIED = "rpg:PlayerDied"
    MOB_DIED = "rpg:MobDied"
    PLAYER_MODIFY_WEAPON = "rpg:PlayerModifyWeapon"
    PLAYER_MODIFY_RELIC = "rpg:PlayerModifyRelic"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


# TODO: 仅广播玩家直接攻击生物， 不计算效果攻击、 饰品攻击等
@dataclass
class PlayerAttackMobEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    attack_data: AttackData
    damages: list[int]
    is_crit: bool
    type = BroadcastType.PLAYER_ATTACK_MOB


@dataclass
class MobAttackPlayerEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    attack_data: AttackData
    damages: list[int]
    type = BroadcastType.MOB_ATTACK_PLAYER


@dataclass
class PlayerAttackPlayerEvent(BaseEvent):
    player: "PlayerEntity"
    target: "PlayerEntity"
    attack_data: AttackData
    damages: list[int]
    is_crit: bool
    type = BroadcastType.PLAYER_ATTACK_PLAYER


@dataclass
class PlayerKillMobEvent(BaseEvent):
    player: "PlayerEntity"
    mob: "MobEntity"
    type = BroadcastType.PLAYER_KILL_MOB
    drop_item = True
    drop_exp = True

    def cancel_dropitem(self):
        self.drop_item = False

    def cancel_dropexp(self):
        self.drop_exp = False


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


@dataclass
class MobInitedEvent(BaseEvent):
    mob: "MobEntity"
    type = BroadcastType.MOB_INITED


@dataclass
class MobDiedEvent(BaseEvent):
    mob: "MobEntity"
    type = BroadcastType.MOB_DIED
    drop = True

    def cancel_drop(self):
        self.drop = False


@dataclass
class PlayerDiedEvent(BaseEvent):
    player: "PlayerEntity"
    type = BroadcastType.PLAYER_DIED


@dataclass
class PlayerUseSkillEvent(BaseEvent):
    player: "PlayerEntity"
    type = BroadcastType.PLAYER_USE_SKILL


# @dataclass
# class PlayerSetSkillEvent(BaseEvent):
#     player: "PlayerEntity"
#     type = BroadcastType.PLAYER_SET_SKILL


@dataclass
class PlayerUseUltEvent(BaseEvent):
    player: "PlayerEntity"
    type = BroadcastType.PLAYER_USE_ULT


# @dataclass
# class PlayerSetUltEvent(BaseEvent):
#     player: "PlayerEntity"
#     type = BroadcastType.PLAYER_SET_ULT


@dataclass
class PlayerModifyWeaponEvent(BaseEvent):
    player: Player
    index: int
    slotitem: "SlotItem | None"
    type = BroadcastType.PLAYER_MODIFY_WEAPON
    "接收道事件之后返回字符串可以阻止装备武器并返回原因"


@dataclass
class PlayerModifyRelicEvent(BaseEvent):
    player: Player
    index: int
    slotitem: "SlotItem | None"
    type = BroadcastType.PLAYER_MODIFY_RELIC
    "接收道事件之后返回字符串可以阻止装备饰品并返回原因"
