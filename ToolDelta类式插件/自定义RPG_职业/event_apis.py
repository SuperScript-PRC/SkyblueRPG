from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast, Player

# if TYPE_CHECKING:
#     from . import SlotItem


class BroadcastType(str, Enum):
    PLAYER_FINISH_JOB = "rpg:PlayerFinishJob"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerFinishJobEvent(BaseEvent):
    "玩家完成工作"

    player: "Player"
    job_name: str
    salary: int
    added_exp: int
    type = BroadcastType.PLAYER_FINISH_JOB
