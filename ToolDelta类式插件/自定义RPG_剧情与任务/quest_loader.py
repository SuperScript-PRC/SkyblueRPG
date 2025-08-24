"big quest loader"

import os
import sys
import json
import importlib
from types import ModuleType
from pathlib import Path
from typing import TYPE_CHECKING
from collections.abc import Callable
from tooldelta import cfg, fmts, Player

from .define import ShopSell, ShopSellMeta

if TYPE_CHECKING:
    from . import CustomRPGPlotAndTask, BroadcastListenerCB
    from .plot_utils import Dialogue


QUEST_STD = {
    "显示名": str,
    "子任务": cfg.AnyKeyValue(
        {
            "描述": str,
            cfg.KeyGroup("优先级"): int,
            "任务达成条件检测的指令": cfg.JsonList(str),
            "只能由命令方块触发": bool,
            cfg.KeyGroup("坐标"): cfg.JsonList(int, 3),
            "任务达成条件高级设置(没有就填{})": [
                type(None),
                {
                    cfg.KeyGroup("需要的物品的标签名及数量"): cfg.AnyKeyValue(cfg.PInt),
                    cfg.KeyGroup("需要完成的前置剧情名列表"): cfg.JsonList(str),
                },
            ],
            "任务模式(-1=一次性 0=可重复做 >0为任务冷却秒数)": int,
            "任务完成": {
                "执行的指令": cfg.JsonList(str),
                "给予的[RPG特殊物品标签名:数量](没有就填{})": cfg.AnyKeyValue(cfg.PInt),
                "触发的剧情的标签名(没有则填null)": (type(None), str),
                "开始的新任务名(没有则填null)": (type(None), str),
            },
        },
    ),
}
SYSTEM: "CustomRPGPlotAndTask | None" = None

# always dynamic
now_loading: Path
now_plotpath: str


class _plotpath:
    def __truediv__(self, other: str) -> str:
        return now_plotpath + ":" + other


plotpath = _plotpath()


def get_system() -> "CustomRPGPlotAndTask":
    if SYSTEM is None:
        raise RuntimeError("SYSTEM is not initialized")
    return SYSTEM


def format_name(basepath: Path, tagname: str):
    return f"{basepath.parent.name}/{basepath.name}:{tagname}"


class RegisteredPlot:
    def __init__(
        self,
        tagname: str,
        linked_to: str,
        pfunc: Callable[[Player], None],
        disposable: bool,
        force_play: bool,
    ):
        """
        已注册剧情

        Args:
            basename (str): 分组名
            tagname (str): 标签名
            linked_to (str): 关联到的剧情触发点
            pfunc (Callable[["CustomRPGPlotAndTask"s, Player], None]): 剧情播放方法
            disposable (bool): 是否为一次性剧情
            force_play (bool): 是否在玩家重进游戏时强制从头播放
        """
        self._tagname = tagname
        self.linked_to = linked_to
        self.pfunc = pfunc
        self.disposable = disposable
        self._section_text: str | None = None
        self._cond_cb: Callable[[Player], bool] | None = None
        get_system()._regist_plot(self)

    def set_as_main(self):
        "将此剧情作为剧情触发点的主剧情。"
        if self.linked_to == "":
            raise ValueError("此剧情不支持设置")
        get_system()._regist_main_plot(self)

    def set_insertion(self, cond: Callable[[Player], bool]):
        """
        将此剧情作为一个插入的剧情项。

        Args:
            cond (Callable[["CustomRPGPlotAndTask", Player], bool]): 条件判断回调, 成功则插入剧情
        """
        if self.linked_to == "":
            raise ValueError("此剧情不支持设置")
        self._cond_cb = lambda player: cond(player)
        get_system()._add_plot_insertion(self)

    def set_choice_insertion(self, section_text: str, cond: Callable[[Player], bool]):
        """
        将此剧情作为一个插入的可选剧情项。

        Args:
            section_text (str): 可选剧情项选项文本
            cond (Callable[["CustomRPGPlotAndTask", Player], bool]): 条件判断回调, 成功则插入选项
        """
        if self.tagname == "" or self.linked_to == "":
            raise ValueError("此剧情不支持设置")
        self._cond_cb = lambda player: cond(player)
        self._section_text = section_text
        get_system()._add_plot_choice_insertion(self)

    def _get_extra_choice_insertions(self):
        return get_system().choicable_inserted_plots.get(self.linked_to, [])

    def get_available_choices_insertions(self, target: Player):
        plots = self._get_extra_choice_insertions()
        valid: list[RegisteredPlot] = []
        for plot in plots:
            cb = plot._cond_cb
            assert cb, "plot._cond_cb is None"
            if cb(target):
                if plot in valid:
                    fmts.print_war(f"自定义剧情与任务: 重复的剧情: {plot}")
                valid.append(plot)
        return valid

    def run(self, player: Player):
        insertions = get_system()._get_insertions(self.linked_to)
        for insertion_plot in insertions:
            if insertion_plot == self:
                continue
            cb = insertion_plot._cond_cb
            if cb is None:
                raise ValueError(f"{insertion_plot.tagname} cond_cb is None")
            if cb(player):
                return insertion_plot.run(player)
        # choicable_plots = get_system().choicable_inserted_plots.get(self.linked_to, [])
        # choices: list[RegisteredPlot] = []
        # for choicable_plot in choicable_plots:
        #     cb = choicable_plot._cond_cb
        #     if cb is None:
        #         raise ValueError(f"{choicable_plot.tagname} cond_cb is None")
        #     if cb(player):
        #         choices.append(choicable_plot)
        self.pfunc(player)
        return self

    def __repr__(self):
        return f"RegisteredPlot({self.pfunc.__name__})"

    @property
    def raw_name(self):
        return self.pfunc.__name__

    @property
    def tagname(self):
        return self._tagname or self.raw_name


def set_system(sys: "CustomRPGPlotAndTask"):
    global SYSTEM
    SYSTEM = sys


def plot(
    tagname: str = "",
    linked_to: str = "",
    *,
    disposable: bool = False,
    force_play: bool = False,
):
    """
    注册剧情

    Args:
        tagname (str): 剧情标签名
        linked_to (str): 关联到的剧情触发点
        disposable (bool, optional): 是否为一次性剧情. Defaults to False.
        force_play (bool): 是否在玩家重进游戏时强制从头播放
    """

    def receiver(pfunc: Callable[[Player], None]):
        p = RegisteredPlot(
            format_name(now_loading, tagname), linked_to, pfunc, disposable, force_play
        )
        return p

    return receiver


def dialogue(
    linked_to: str,
    npc_name: str,
    disposable: bool = False,
    force_play: bool = False,
):  # -> Callable[..., RegisteredPlot]:
    _Dialogue = get_system().putils.Dialogue

    def receiver(pfunc: Callable[["Dialogue"], None]):
        def wrapper(player: Player):
            pfunc(_Dialogue(player, npc_name))

        wrapper.__name__ = pfunc.__name__
        p = RegisteredPlot(
            format_name(now_loading, ""), linked_to, wrapper, disposable, force_play
        )
        return p

    return receiver


def load_project(basepath: Path):
    global now_loading, now_plotpath
    quest_json_path = basepath / "quests.json"
    system = get_system()
    now_loading = basepath
    now_plotpath = basepath.parent.name + "/" + basepath.name
    if quest_json_path.is_file():
        with open(quest_json_path, encoding="utf-8") as f:
            content = json.load(f)
        cfg.check_auto(QUEST_STD, content)
        disp_name = content["显示名"]
        for sub_tagname, quest_raw in content["子任务"].items():
            tname = format_name(basepath, sub_tagname)
            quest = system.RPGQuest(
                tag_name=tname,
                show_name=disp_name,
                priority=quest_raw.get(r"优先级", 1),
                description=quest_raw[r"描述"],
                position=tuple(p) if (p := quest_raw.get(r"坐标")) else None,
                detect_cmds=quest_raw[r"任务达成条件检测的指令"],
                mode=quest_raw[r"任务模式(-1=一次性 0=可重复做 >0为任务冷却秒数)"],
                advance_mode=quest_raw[r"任务达成条件高级设置(没有就填{})"] is not None,
                need_item=quest_raw[r"任务达成条件高级设置(没有就填{})"].get(
                    r"需要的物品的标签名及数量", None
                ),
                need_plot=quest_raw[r"任务达成条件高级设置(没有就填{})"].get(
                    r"需要完成的前置剧情名列表", None
                ),
                exec_cmds_when_finished=quest_raw[r"任务完成"][r"执行的指令"],
                items_give_when_finished=quest_raw[r"任务完成"][
                    r"给予的[RPG特殊物品标签名:数量](没有就填{})"
                ],
                run_plot_when_finished=quest_raw[r"任务完成"][
                    r"触发的剧情的标签名(没有则填null)"
                ],
                # quest_raw[r"任务完成"][r"开始的新任务名(没有则填null)"],
                command_block_only=quest_raw[r"只能由命令方块触发"],
            )
            system.quests[tname] = quest
    bp = os.path.basename(basepath)
    dp = os.path.dirname(basepath)
    sys.path.append(dp)
    module_name = bp + ".plots"
    old_modules = sys.modules.copy()
    module = importlib.import_module(module_name)
    if module_name in old_modules.keys():
        importlib.reload(module)
    sys.path.remove(dp)


def load_projects():
    ld = 0
    sys = get_system()
    for first_name in Path(sys.format_data_path(sys.SPECIAL_QUEST_PATH)).iterdir():
        if first_name.is_dir():
            for second_name in first_name.iterdir():
                if second_name.is_dir() and not second_name.name.startswith("__"):
                    load_project(second_name)
                    ld += 1
    fmts.print_inf(f"加载了 {ld} 个大型剧情组.")


def as_broadcast_listener(
    bound_quest: "CustomRPGPlotAndTask.LegacyQuest", event_name: str
):
    "(System, Player, EventName, DataDict)"

    def _wrapper(func: "BroadcastListenerCB"):
        bl = get_system().BroadcastListener(bound_quest, event_name, func)
        get_system().quests_bound_listeners.setdefault(bound_quest, []).append(bl)

    return _wrapper


class dev_customrpg_plot(ModuleType):
    "this is a fake module"

    def __init__(self):
        super().__init__("dev_customrpg_plot")

    plot = staticmethod(plot)
    dialogue = staticmethod(dialogue)
    plotpath = plotpath
    as_broadcast_listener = staticmethod(as_broadcast_listener)
    get_system = staticmethod(get_system)
    ShopSell = ShopSell
    ShopSellMeta = ShopSellMeta

    @property
    def Dialogue(self):
        return get_system().putils.Dialogue


loader_module = dev_customrpg_plot()

sys.modules["dev_customrpg_plot"] = loader_module
