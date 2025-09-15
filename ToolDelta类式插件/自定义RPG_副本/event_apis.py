from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

if TYPE_CHECKING:
    from .frame_dungeon import Dungeon, DungeonFinishType


class BroadcastType(str, Enum):
    PLAYER_START_DUNGEON_EVENT = "rpg:PlayerStartDungeonEvent"
    PLAYER_FINISH_DUNGEON_EVENT = "rpg:PlayerFinishDungeonEvent"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerStartDungeonEvent(BaseEvent):
    "玩家开启副本"

    player: "Player"
    dungeon: "Dungeon"
    type = BroadcastType.PLAYER_START_DUNGEON_EVENT


@dataclass
class PlayerFinishDungeonEvent(BaseEvent):
    "玩家完成副本 (无论胜利或否)"

    player: "Player"
    dungeon: "Dungeon"
    finish_type: "DungeonFinishType"
    time_cost: float
    type = BroadcastType.PLAYER_FINISH_DUNGEON_EVENT
