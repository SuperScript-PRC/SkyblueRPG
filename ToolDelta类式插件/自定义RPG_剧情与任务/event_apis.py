from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

if TYPE_CHECKING:
    from . import Item


class BroadcastType(str, Enum):
    PlayerTradingWithNPC = "rpg:PlayerTradingWithNPC"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerTradingWithNPCEvent(BaseEvent):
    "玩家与NPC进行交易"

    player: "Player"
    buy_item: "Item"
    buy_amount: int
    sell_item: "Item"
    sell_amount: int
    type = BroadcastType.PlayerTradingWithNPC
