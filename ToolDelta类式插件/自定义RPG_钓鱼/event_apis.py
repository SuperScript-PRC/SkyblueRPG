from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from tooldelta import InternalBroadcast, Player

if TYPE_CHECKING:
    from . import SlotItem


class BroadcastType(str, Enum):
    PLAYER_FISH_HOOKED = "rpg:PlayerFishHooked"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerFishHookedEvent(BaseEvent):
    "玩家钓鱼上钩"

    player: "Player"
    hooked_item: list["SlotItem"]
    not_empty: bool
    type = BroadcastType.PLAYER_FISH_HOOKED
