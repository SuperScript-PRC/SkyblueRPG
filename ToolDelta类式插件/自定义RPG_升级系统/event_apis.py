from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast, Player, TYPE_CHECKING

if TYPE_CHECKING:
    from . import SlotItem


class BroadcastType(str, Enum):
    PLAYER_UPGRADE_OBJECT = "rpg:PlayerUpgradeObject"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerUpgradeObjectEvent(BaseEvent):
    "玩家升级道具"

    player: "Player"
    upgraded_item: "SlotItem"
    type = BroadcastType.PLAYER_UPGRADE_OBJECT
