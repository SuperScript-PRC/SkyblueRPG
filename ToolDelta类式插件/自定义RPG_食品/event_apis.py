from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast, Player
from .food_frame import RPGFood


class BroadcastType(str, Enum):
    PLAYER_EAT = "rpg:PlayerEat"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerEatEvent(BaseEvent):
    "玩家食用食物"

    player: "Player"
    food: RPGFood
    type = BroadcastType.PLAYER_EAT
