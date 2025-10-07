from enum import Enum
from dataclasses import dataclass
from tooldelta import InternalBroadcast, Player


class BroadcastType(str, Enum):
    PlayerStartReading = "sr.reader:PlayerStartReading"
    PlayerReadFinished = "sr.reader:PlayerReadFinished"
    PlayerExitReading = "sr.reader:PlayerExitReading"


class BaseEvent:
    type: BroadcastType

    def to_broadcast(self):
        return InternalBroadcast(self.type, self)


@dataclass
class PlayerStartReadingEvent(BaseEvent):
    "玩家开始阅读书籍内容"

    player: "Player"
    text_tagname: str
    type = BroadcastType.PlayerStartReading


@dataclass
class PlayerReadFinishedEvent(BaseEvent):
    "玩家阅读完书籍内容"

    player: "Player"
    text_tagname: str
    type = BroadcastType.PlayerReadFinished


@dataclass
class PlayerExitReadingEvent(BaseEvent):
    "玩家退出阅读"

    player: "Player"
    text_tagname: str
    type = BroadcastType.PlayerExitReading
