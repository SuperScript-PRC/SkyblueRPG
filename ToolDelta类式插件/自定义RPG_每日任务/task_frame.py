import time
import random
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Protocol, Any
from tooldelta import Player, InternalBroadcast, utils

if TYPE_CHECKING:
    from . import CustomRPGDailyTask


class DailyTask(metaclass=ABCMeta):
    def __init_subclass__(cls, disp_name: str, points: int = 12):
        cls.disp_name = disp_name
        cls.points = points

    @staticmethod
    @abstractmethod
    def load_to_system(system: "CustomRPGDailyTask") -> None:
        raise NotImplementedError

    def __init__(self, parent: "DailyTasksManager", player: Player, data: dict):
        self.parent = parent
        self.sys = parent.sys
        self.player = player
        self.data = data
        self._PlayerEntityType = self.sys.rpg.PlayerEntity
        self._finished = self.is_finished()

    @abstractmethod
    def OnEvent(self, event: "BaseEvent", player: Player):
        raise NotImplementedError

    @classmethod
    def CanBeAdded(cls, player: Player):
        return True

    @abstractmethod
    def Display(self) -> str:
        raise NotImplementedError

    def _is_my_event(self, event: "BaseEvent"):
        if self._finished:
            return False
        if hasattr(event, "player"):
            player = getattr(event, "player")
            if isinstance(player, self._PlayerEntityType):
                return self.player is player.player
            elif isinstance(player, Player):
                return self.player is player
        return False

    def finish(self):
        self.data.clear()
        self.data["last_finish_time"] = nowday()
        self.sys.rpg.show_succ(self.player, f" 每日任务已完成： {self.disp_name}")
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run playsound random.levelup @s ~~~ 1 0.5"
        )
        self._finished = True
        self.parent.add_points(self.points)

    def is_finished(self):
        return nowday() == self.data.get("last_finish_time", 0)

    def display_as_line(self):
        status = "§a已完成" if self._finished else self.Display()
        return simple_align(self.disp_name, 20) + status

    @property
    def name(self):
        return self.__class__.__name__


class DailyTasksManager:
    def __init__(self, sys: "CustomRPGDailyTask", player: Player):
        self.sys = sys
        self.player = player
        self.tasks: list[DailyTask] = []
        self.points = 0
        self.load()

    def recv_event(self, evt: InternalBroadcast):
        for task in self.tasks:
            if task._is_my_event(evt.data):
                task.OnEvent(evt.data, self.player)

    def load(self):
        self.datas = utils.tempjson.load_and_read(
            self.sys.format_player_data_path(self.player),
            need_file_exists=False,
            default={},
        )
        if self.datas.get("last-flush-day", 0) != nowday():
            chosen_tasks = [
                i for i in self.sys.tasks.values() if i.CanBeAdded(self.player)
            ]
            self.tasks = [
                t(self, self.player, self.datas.get(t.name, {}))
                for t in choice_tasks(chosen_tasks)
            ]
            self.points = 0
            self.datas["last-flush-day"] = nowday()
        else:
            for tname in self.datas.get("tasks", []):
                t = self.sys.tasks.get(tname)
                if t is None:
                    continue
                self.tasks.append(t(self, self.player, self.datas.get(tname, {})))
            self.points = self.datas.get("points", 0)

    def unload(self):
        for task in self.tasks:
            self.datas[task.name] = task.data
        self.datas["tasks"] = [i.name for i in self.tasks]
        self.datas["points"] = self.points
        utils.tempjson.load_and_write(
            self.sys.format_player_data_path(self.player),
            self.datas,
            need_file_exists=False,
        )

    def display(self):
        self.sys.rpg.show_any(self.player, "d", "正在进行的每日任务：")
        for task in self.tasks:
            self.sys.rpg.show_inf(
                self.player,
                " §7₊"
                + self.sys.bigchar.small_number(task.points)
                + "§f "
                + task.display_as_line(),
            )
        a = int(self.points / 64 * 30)
        self.sys.rpg.show_any(
            self.player,
            "d",
            "活跃值： §a"
            + "·" * a
            + "§7"
            + "·" * (30 - a)
            + f" §a{self.points}§7/"
            + self.sys.bigchar.small_number(64),
        )

    def add_points(self, points: int):
        addPlayerStore = self.sys.rpg.backpack_holder.giveItem
        createItem = self.sys.rpg.item_holder.createItem
        self.points = min(64, self.points + points)
        a = int(self.points / 64 * 30)
        self.sys.rpg.show_any(
            self.player, "d", "活跃值： §a" + "·" * a + "§7" + "·" * (30 - a)
        )
        addPlayerStore(self.player, createItem("蔚晶", points))
        if self.points >= 64:
            self.points -= 64
            self.sys.rpg.show_succ(self.player, " 今日活跃值已满！")


class BaseEvent(Protocol):
    type: Any


ZHCN_START = 0x4E00
ZHCN_END = 0x9FA5


def simple_calculate_length(text: str) -> int:
    return sum(
        1 + (1 if ord(i) >= ZHCN_START and ord(i) <= ZHCN_END else 0) for i in text
    )


def simple_align(text: str, space: int):
    return text + " " * (space - simple_calculate_length(text))


def nowday():
    return int(time.mktime(time.localtime()) // 86400)


def choice_tasks(tasks: list["type[DailyTask]"], count: int = 5):
    random.seed(nowday())
    tasks = tasks.copy()
    selected_tasks: list["type[DailyTask]"] = []
    while count > 0 and tasks:
        t = random.choice(tasks)
        tasks.remove(t)
        selected_tasks.append(t)
        count -= 1
    return selected_tasks


def get_task_classes_from_module(sys: "CustomRPGDailyTask", module):
    classes: dict[str, type[DailyTask]] = {}
    for k, v in module.__dict__.items():
        if isinstance(v, type) and issubclass(v, DailyTask) and v != DailyTask:
            classes[k] = v
            v.load_to_system(sys)
    return classes
