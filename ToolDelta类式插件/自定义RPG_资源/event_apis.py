from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

if TYPE_CHECKING:
    from . import SourcePoint


class BroadcastType(str, Enum):
    PLAYER_DIG_SOURCE = "rpg:PlayerDigSource"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerDigSourceEvent(BaseEvent):
    "玩家采掘资源"

    player: "Player"
    source_point: "SourcePoint"
    first_collected: bool
    type = BroadcastType.PLAYER_DIG_SOURCE
