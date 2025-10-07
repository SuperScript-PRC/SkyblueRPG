import time
from dataclasses import dataclass
from tooldelta import Player
from .define import DEFAULT_MAX_SHAKE_VALUE, NewRecordEnum
from .frame_levels import LevelType, Level

if 0:
    from . import CustomRPGRogue
    from .rogue import Executor


@dataclass
class RogueStatusStorage:
    sys: "CustomRPGRogue"
    executor: "Executor"
    start_time_unix: int
    player: Player
    phase: int
    shake_value: int
    max_shake_value: int
    score: int
    current_level: Level | None
    next_levels: list[Level]
    current_level_passed: bool
    passed_levels: list[LevelType]
    pos: tuple[int, int, int]
    interrupted: bool

    @classmethod
    def default(cls, sys: "CustomRPGRogue", player: Player):
        return cls(
            sys=sys,
            executor=sys.executor,
            player=player,
            start_time_unix=int(time.time()),
            phase=0,
            shake_value=0,
            max_shake_value=DEFAULT_MAX_SHAKE_VALUE,
            score=0,
            current_level=None,
            next_levels=[],
            current_level_passed=False,
            passed_levels=[],
            pos=(0, 0, 0),
            interrupted=False,
        )

    @classmethod
    def from_dict(cls, sys: "CustomRPGRogue", player: Player, dic: dict):
        obj = cls(
            sys=sys,
            executor=sys.executor,
            player=player,
            start_time_unix=dic["start_time_unix"],
            passed_levels=[LevelType(lt) for lt in dic["passed_levels"]],
            phase=dic["phase"],
            shake_value=dic["shake_value"],
            max_shake_value=dic["max_shake_value"],
            score=dic["score"],
            current_level=None,
            next_levels=[],
            current_level_passed=dic["current_level_passed"],
            pos=(dic["pos"][0], dic["pos"][1], dic["pos"][2]),
            interrupted=dic["interrupted"],
        )
        obj.current_level = (
            Level.load(obj, dic["current_level"]) if dic["current_level"] else None
        )
        obj.next_levels = [Level.load(obj, i) for i in dic["next_levels"]]
        return obj

    def to_dict(self):
        return {
            "start_time_unix": self.start_time_unix,
            "phase": self.phase,
            "shake_value": self.shake_value,
            "max_shake_value": self.max_shake_value,
            "score": self.score,
            "current_level": self.current_level.dump() if self.current_level else None,
            "next_levels": [lt.dump() for lt in self.next_levels],
            "current_level_passed": self.current_level_passed,
            "passed_levels": [lt.value for lt in self.passed_levels],
            "pos": [self.pos[0], self.pos[1], self.pos[2]],
            "interrupted": self.interrupted,
        }

    def add_shake_value(self, val: int):
        self.shake_value += val

    def reduce_shake_value(self, val: int):
        self.shake_value -= val

    def add_score(self, val: int):
        self.score += val

    def add_passed_level(self, lt: LevelType):
        self.passed_levels.append(lt)

    def change_current_level(self, level: Level):
        self.current_level = level

    def interrupt(self):
        self.interrupted = True

    @property
    def passed_levels_num(self):
        return len(self.passed_levels)

    @property
    def money(self):
        return self.sys.rpg.api_holder.getItemCount(self.player, "r:金粒")

    @property
    def effects_amount(self):
        return len(
            self.sys.rpg.api_holder.get_player_entity(self.player).get_effects_by_tag(
                "reflect_world"
            )
        )

    def to_record(self):
        return RogueRecord(
            playername=self.player.name,
            xuid=self.player.xuid,
            record_time_unix=int(time.time()),
            final_money=self.sys.rpg.api_holder.getItemCount(self.player, "r:金粒"),
            clear_time=int(time.time() - self.start_time_unix),
            final_score=self.score,
            images_amount=self.passed_levels_num,
            effects_amount=self.effects_amount,
        )

    def save(self):
        self.sys.write_storage(self)


@dataclass
class RogueRecord:
    playername: str
    xuid: str
    record_time_unix: int
    final_money: int
    clear_time: int
    final_score: int
    images_amount: int
    effects_amount: int

    def to_dict(self):
        return {
            "playername": self.playername,
            "xuid": self.xuid,
            "record_time_unix": self.record_time_unix,
            "final_money": self.final_money,
            "clear_time": self.clear_time,
            "final_score": self.final_score,
            "images_amount": self.images_amount,
            "effects_amount": self.effects_amount,
        }

    @classmethod
    def from_dict(cls, xuid: str, dic: dict):
        new = cls(
            playername=dic["playername"],
            xuid=xuid,
            record_time_unix=dic["record_time_unix"],
            final_money=dic["final_money"],
            clear_time=dic["clear_time"],
            final_score=dic["final_score"],
            images_amount=dic["images_amount"],
            effects_amount=dic["effects_amount"],
        )
        return new

    def update_old(self, old: "RogueRecord | None"):
        r = 0
        if old is not None:
            if self.final_money > old.final_money:
                r |= NewRecordEnum.Money
                old.final_money = self.final_money
            if self.clear_time < old.clear_time:
                r |= NewRecordEnum.ClearTime
                old.clear_time = self.clear_time
            if self.final_score > old.final_score:
                r |= NewRecordEnum.Score
                old.final_score = self.final_score
            if self.images_amount > old.images_amount:
                r |= NewRecordEnum.ImagesAmount
                old.images_amount = self.images_amount
        return old or self, r
