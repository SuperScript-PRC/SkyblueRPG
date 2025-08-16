from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast, Player, TYPE_CHECKING

if TYPE_CHECKING:
    from . import SlotItem


class BroadcastType(str, Enum):
    PLAYER_FIX_OBJECT = "rpg:PlayerRepairObject"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerRepairObjectEvent(BaseEvent):
    "玩家修补物品"

    player: "Player"
    repaired_item: "SlotItem"
    cost_material_tagname: str
    cost_material_amount: int
    cost_extra_materials: dict[str, int]
    type = BroadcastType.PLAYER_FIX_OBJECT
