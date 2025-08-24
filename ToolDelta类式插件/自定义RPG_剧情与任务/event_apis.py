from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

if TYPE_CHECKING:
    from .define import ShopSell, ShopSellMeta


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
    buy_data: "ShopSell | ShopSellMeta"
    type = BroadcastType.PlayerTradingWithNPC
