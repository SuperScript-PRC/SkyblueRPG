from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast

if 0:
    from .frame import MiniGameStage


class BroadcastType(str, Enum):
    PlayerStartGame = "rpg-games:PlayerStartGame"
    PlayerGameLevelUp = "rpg-games:PlayerGameLevelUp"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class StageStart(BaseEvent):
    "玩家开始游戏"

    stage: "MiniGameStage"
    from_prev_level: bool
    type = BroadcastType.PlayerStartGame


@dataclass
class StageFinished(BaseEvent):
    "玩家游戏过关"

    stage: "MiniGameStage"
    continued: bool
    type = BroadcastType.PlayerGameLevelUp
