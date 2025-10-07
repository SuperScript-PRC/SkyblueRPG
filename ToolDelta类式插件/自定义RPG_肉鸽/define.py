from dataclasses import dataclass
from enum import Enum, IntEnum

if 0:
    from . import entry
    from ..自定义RPG_剧情与任务.quest_loader import RegisteredPlot

    RPGEffect = entry.rpg.frame_effects.RPGEffect

DEFAULT_MAX_SHAKE_VALUE = 200


class LevelType(IntEnum):
    Entrance = 0
    PVE = 1
    Fortune = 2
    Award = 3
    Rest = 4
    Trade = 5
    Boss = 6


class AreaType(IntEnum):
    Entrance = 0
    PVE = 1
    Fortune = 2
    Award = 3
    Rest = 4
    Trade = 5
    Boss = 6


AREA_NAME = {
    AreaType.Entrance: "入口",
    AreaType.PVE: "战斗",
    AreaType.Fortune: "机遇",
    AreaType.Award: "奖励关",
    AreaType.Rest: "休憩",
    AreaType.Trade: "交易",
    AreaType.Boss: "怪王",
}


LEVELTYPE_TO_NPCNAME = {
    LevelType.PVE: "RNPC_战斗",
    LevelType.Fortune: "RNPC_机遇",
    LevelType.Award: "RNPC_奖励关",
    LevelType.Rest: "RNPC_休憩",
    LevelType.Trade: "RNPC_交易",
    LevelType.Boss: "RNPC_首领",
}


class MobWave:
    def __init__(self, *mob_and_amount: tuple[str, int]):
        self.mob_and_amount = mob_and_amount


@dataclass
class FortuneEvent:
    plot: "RegisteredPlot"
    weight: float


class CBEvent(Enum):
    PlayerStartRogue = r"rogue.start_game"
    PlayerSelectNextLevel = r"rogue.player_select_nextlevel"
    PlayerSupplyHealth = r"rogue.player_supply_health"
    PlayerGameCompletion = r"rogue.player_game_completion"


class NewRecordEnum(IntEnum):
    Score = 1 << 1
    Money = 1 << 2
    ClearTime = 1 << 3
    ImagesAmount = 1 << 4
    EffectsAmount = 1 << 5
