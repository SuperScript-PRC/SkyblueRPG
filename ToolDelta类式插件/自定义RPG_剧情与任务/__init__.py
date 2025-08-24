import os
import time
import json
import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar
from tooldelta import (
    Plugin,
    InternalBroadcast,
    utils,
    cfg as config,
    fmts,
    game_utils,
    Player,
    TYPE_CHECKING,
    plugin_entry,
)

from tooldelta.utils import chatbar_lock_list
from . import plot_utils, quest_loader, event_apis

importlib.reload(quest_loader)
importlib.reload(plot_utils)

DATA_DICT = dict
T = TypeVar("T")
CALLTYPE = T | Callable[[Player, DATA_DICT], T]
BROADCAST_DATA = Any
BroadcastListenerCB = Callable[[Player, BROADCAST_DATA, DATA_DICT], None]


def acall(func: CALLTYPE[T], player: Player, data_dict: DATA_DICT) -> T:
    if isinstance(func, Callable):
        return func(player, data_dict)
    else:
        return func


@dataclass(frozen=True)
class LegacyQuest:
    tag_name: str
    disp_name: str
    priority: int
    "任务优先级, 也可以理解为任务的等级"
    description: CALLTYPE[str]
    position: CALLTYPE[tuple[int, int, int]] | None
    cooldown: int | None
    "为 0 则为可重复接取; 为 None 则为一次性任务"
    add_quest_cb: Callable[[Player], tuple[bool, str]] | None
    detect_cb: Callable[[Player, DATA_DICT], tuple[bool, str]] | None
    finish_cb: Callable[[Player, DATA_DICT], None] | None


class QuestDataMaintainer:
    def __init__(self, player: Player, quest: LegacyQuest, readonly=False):
        self.quest = quest
        self.player = player
        self.readonly = readonly

    def __enter__(self):
        self.data = entry.read_quest_datas(self.player).get(self.quest.tag_name, {})
        self.haskey = self.data != {}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.readonly:
            _datas = entry.read_quest_datas(self.player)
            if self.quest.tag_name in _datas or (not self.haskey and self.data != {}):
                _datas[self.quest.tag_name] = self.data
                entry.save_quest_datas(self.player, _datas)


def RPGQuest(
    tag_name: str,
    show_name: str,
    priority: int,
    description: str,
    position: tuple[int, int, int] | None,
    detect_cmds: list[str],
    mode: int,
    advance_mode: bool,
    need_item: dict[str, int] | None = {},
    need_plot: list[str] | None = [],
    exec_cmds_when_finished: list[str] = [],
    items_give_when_finished: dict = {},
    run_plot_when_finished: str | None = "",
    command_block_only: bool = False,
):
    system = entry

    def detect(player: Player, _):
        if command_block_only:
            return (False, "§6任务条件未达成")
        failed_reasons = []
        for check_cmd in detect_cmds:
            if not game_utils.isCmdSuccess(check_cmd.replace("[玩家名]", player.name)):
                failed_reasons.append("任务条件未满足")
        if advance_mode:
            if need_item:
                for item_tag, count in need_item.items():
                    result = system.rpg.backpack_holder.getItem(player, item_tag)
                    if result is None or result.count < count:
                        items_to_get = system.rpg.item_holder.createItems(
                            item_tag, count
                        )
                        count = (
                            len(items_to_get)
                            if items_to_get[0].item.stackable
                            else items_to_get[0].count
                        )
                        item_to_get = items_to_get[0]
                        if result is None:
                            failed_reasons.append(
                                f"§6需要 {item_to_get.disp_name} §c0§f/{count}"
                            )
                        else:
                            failed_reasons.append(
                                f"§6需要 {item_to_get.disp_name} §c{result.count}§f/{count}"
                            )
            if need_plot:
                player_finished_plot = system.check_plot_record(player).keys()
                for plot in need_plot:
                    if plot not in player_finished_plot:
                        failed_reasons.append("§6还有剧情未完成")
                        break
        if failed_reasons == []:
            return True, ""
        else:
            return False, "\n".join(failed_reasons)

    def finish(player: Player, _):
        for cmd in system.cfg["任务设置"]["任务完成执行的指令"]:
            system.game_ctrl.sendwocmd(
                utils.simple_fmt(
                    {
                        "[玩家名]": player.name,
                        "[任务名]": show_name,
                        "[任务描述]": description,
                    },
                    cmd,
                )
            )
        system.play_quest_finished_sound(player)
        for cmd in exec_cmds_when_finished:
            system.game_ctrl.sendwocmd(utils.simple_fmt({"[玩家名]": player.name}, cmd))
        for item_tag, count in items_give_when_finished.items():
            item = system.rpg.item_holder.createItems(item_tag, count)
            system.rpg.backpack_holder.giveItems(player, item)
        quest_t = run_plot_when_finished
        if quest_t and not quest_t.endswith(".txt"):
            quest_t += ".txt"
        if quest_t and (quest_ := system.get_quest(quest_t)):
            system.add_quest(player, quest_)

    return LegacyQuest(
        tag_name=tag_name,
        disp_name=show_name,
        priority=priority,
        description=description,
        position=position,
        cooldown=(None if mode == -1 else mode),
        add_quest_cb=None,
        detect_cb=detect,
        finish_cb=finish,
    )


class PlotSkipDetector:
    def __init__(self, sys: "CustomRPGPlotAndTask", player: Player):
        self.player = player
        self.dic = sys.snowball_blocking_handler

    def __enter__(self):
        self.dic[self.player.name] = False
        return self

    def __exit__(self, _, _2, _3):
        if self.player.name in self.dic:
            del self.dic[self.player.name]

    def plot_skip(self):
        if self.player.name in self.dic:
            if self.dic[self.player.name]:
                self.dic[self.player.name] = False
                return True
            else:
                return False
        else:
            fmts.print_war(f"剧情跳过: 玩家 {self.player.name} 的剧情跳过被意外中断")
            return True


class BroadcastListener:
    def __init__(
        self,
        bound_quest: LegacyQuest,
        event_name: str,
        cb: BroadcastListenerCB,
    ):
        self.bound_quest = bound_quest
        self.event_name = event_name
        self.cb = cb
        if event_name not in entry.broadcast_listen_events:
            entry.ListenInternalBroadcast(event_name, entry.broadcast_listener)
            entry.broadcast_listen_events.add(event_name)

    @property
    def unique_id(self):
        return self.cb.__name__


class OnlinePlayerBroadcastListener:
    # 代表一个在线玩家的广播侦听器 (当前的所有侦听回调)。
    def __init__(self, player: Player):
        self.player = player
        self.update()

    def active(self, event_name: str, event_data: BROADCAST_DATA):
        for ls in self.broadcast_listeners:
            if ls.event_name == event_name:
                with QuestDataMaintainer(self.player, ls.bound_quest) as m:
                    ls.cb(self.player, event_data, m.data)

    def update(self):
        self.broadcast_listeners: list[BroadcastListener] = []
        quests = entry.read_quests(self.player)
        for quest in quests:
            self.broadcast_listeners.extend(entry.quests_bound_listeners.get(quest, []))


# PLOT_PATH = "剧情脚本"
# QUEST_PATH = "RPG任务"
QUEST_DATA_PATH = "RPG任务数据"
PLOT_REC_PATH = "剧情记录"
DATA_PATH = "数据文件"
SHOP_CD_PATH = "商店补货数据"
SPECIAL_QUEST_PATH = "大型任务"
PLOT_POINT_DATA = "剧情点数据"


class CustomRPGPlotAndTask(Plugin):
    name = "自定义RPG-剧情与任务"
    author = "SuperScript"
    version = (0, 0, 1)

    class PlotExit(Exception):
        def __init__(self, extra: quest_loader.RegisteredPlot | None = None):
            super().__init__()
            self.extra = extra

    class PlotPlayerExit(PlotExit): ...

    class PlotSelectTimeout(PlotExit): ...

    event_apis = event_apis
    BroadcastListener = BroadcastListener
    DATA_PATH = DATA_PATH
    SPECIAL_QUEST_PATH = SPECIAL_QUEST_PATH
    putils = plot_utils
    "剧情播放实用方法"
    LegacyQuest = LegacyQuest
    RPGQuest = staticmethod(RPGQuest)

    def __init__(self, frame):
        super().__init__(frame)
        # self.in_plot_running = {}
        self.snowball_blocking_handler: dict[str, bool] = {}
        self.quests: dict[str, LegacyQuest] = {}
        self.quests_bound_listeners: dict[LegacyQuest, list[BroadcastListener]] = {}
        self.plots: dict[str, quest_loader.RegisteredPlot] = {}
        # 剧情触发点对应的剧情, 唯一
        # dict[linkto, plot]
        self.main_plots: dict[str, quest_loader.RegisteredPlot] = {}
        # 剧情触发点需要插入播放的剧情
        # dict[linkto, plots]
        self.inserted_plots: dict[str, list[quest_loader.RegisteredPlot]] = {}
        # 剧情触发点可选的剧情
        self.choicable_inserted_plots: dict[str, list[quest_loader.RegisteredPlot]] = {}
        # 玩家广播监听触发器
        self.players_broadcast_evts_listeners: dict[
            Player, OnlinePlayerBroadcastListener
        ] = {}
        self.broadcast_listen_events: set[str] = set()
        self.running_plot_threads: dict[Player, utils.ToolDeltaThread] = {}
        self.running_plots: dict[Player, quest_loader.RegisteredPlot] = {}
        for ipath in [
            # PLOT_PATH,
            # QUEST_PATH,
            QUEST_DATA_PATH,
            PLOT_REC_PATH,
            DATA_PATH,
            SHOP_CD_PATH,
            SPECIAL_QUEST_PATH,
            PLOT_POINT_DATA,
        ]:
            os.makedirs(self.data_path / ipath, exist_ok=True)
        CFG_STD = {
            "剧情设置": {
                "说明": str,
                "剧情对话框显示格式": str,
                "选择选项提示格式(未选中)": str,
                "选择选项提示格式(被选中)": str,
                "剧情对话框每行的最多字符数": config.PInt,
            },
            "任务设置": {
                "任务无法提交的显示": {
                    "显示头": str,
                    "任务为一次性任务": str,
                    "任务冷却": str,
                },
                "任务完成执行的指令": config.JsonList(str),
            },
        }
        CFG_DEFAULT = {
            "剧情设置": {
                "剧情对话框显示格式": "§6[角色名]\n§7----------------------------------------\n[内容]",
                "选择选项提示格式(未选中)": "§7[选项序号] §7| §f[选项]",
                "选择选项提示格式(被选中)": "§b[选项序号] §7| §f[选项]",
                "剧情对话框每行的最多字符数": 20,
            },
            "任务设置": {
                "任务无法提交的显示": {
                    "显示头": "§c任务无法达成, 原因: ",
                    "任务为一次性任务": "§c你已经完成过该任务了",
                    "任务冷却": "§c任务冷却时间还有 §6%d §c天 §6%H §c时 §6%M §c分",
                },
                "任务完成执行的指令": [
                    '/tellraw @a[name=[玩家名]] {"rawtext":[{"text":"[任务名]： §a任务完成"}]}',
                    "/execute as @a[name=[玩家名]] at @s run playsound random.levelup @s",
                ],
            },
        }
        self.cfg, _ = config.get_plugin_config_and_version(
            self.name, CFG_STD, CFG_DEFAULT, self.version
        )
        self.ListenPreload(self.on_def, priority=-5)
        self.ListenActive(self.on_inject)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)

    def on_def(self):
        self.intract = self.GetPluginAPI("前置-世界交互")
        self.interper = self.GetPluginAPI("ZBasic", force=False)
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.rpg = self.GetPluginAPI("自定义RPG", force=False)
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        self.tutor = self.GetPluginAPI("自定义RPG-教程")
        self.settings = self.GetPluginAPI("自定义RPG-设置")
        self.spx = self.GetPluginAPI("自定义RPG-特效")
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            from ..前置_世界交互 import GameInteractive
            from ..前置_聊天栏菜单 import ChatbarMenu
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..ZBasic_Lang_中文编程 import ToolDelta_ZBasic
            from ..雪球菜单v3 import SnowMenuV3
            from ..自定义RPG import CustomRPG
            from ..自定义RPG_教程 import CustomRPGTutorial
            from ..自定义RPG_设置 import CustomRPGSettings
            from ..自定义RPG_特效 import FXStageShow

            self.intract: GameInteractive
            self.interper: ToolDelta_ZBasic
            self.snowmenu: SnowMenuV3
            self.rpg: CustomRPG
            self.chatbar: ChatbarMenu
            self.tutor: CustomRPGTutorial
            self.settings: CustomRPGSettings
            self.spx: FXStageShow
            cb2bot: TellrawCb2Bot
        quest_loader.load_projects()
        cb2bot.regist_message_cb(r"sr.plot.trigger", self.handle_plot_run)
        cb2bot.regist_message_cb(r"sr.quest.ok", self.handle_quest_ok)
        cb2bot.regist_message_cb(r"snowball.menu.use", self.handle_snowball_blocking, 2)

    @utils.thread_func("自定义RPG-剧情与任务的游戏初始化")
    def on_inject(self):
        self.chatbar.add_new_trigger(
            [".plotnpc"],
            [],
            "放置NPC剧情触发命令方块(需要创造模式)",
            self.place_npc_plot_cb_at,
            op_only=True,
        )
        self.chatbar.add_new_trigger(
            [".plotput"],
            [],
            "放置剧情触发命令方块(需要创造模式)",
            self.place_plot_cb_at,
            op_only=True,
        )
        self.chatbar.add_new_trigger(
            [".rw", ".任务"],
            [],
            "查看正在进行的任务列表",
            lambda player, _: self.list_player_quests(player) and None,
        )
        self.chatbar.add_new_trigger(
            [".radquest"],
            [("任务标签名", str, None)],
            "强制添加任务",
            self.force_start_quest,
            op_only=True,
        )
        self.chatbar.add_new_trigger(
            [".radques2"],
            [("玩家名", str, None), ("任务标签名", str, None)],
            "为他人强制添加任务",
            self.force_start_quest_for_other,
            op_only=True,
        )
        self.chatbar.add_new_trigger(
            [".rfnquest"],
            [("任务标签名", str, None)],
            "强制完成任务",
            self.force_finish_quest,
            op_only=True,
        )
        self.chatbar.add_new_trigger(
            [".rrmquest"],
            [("任务标签名", str, None)],
            "强制移除任务记录",
            self.force_remove_quest_record,
            op_only=True,
        )
        self.snowmenu.register_main_page(self.handle_quests_menu, "任务列表")
        for player in self.frame.get_players().getAllPlayers():
            self.init_player(player)
        chatbar_lock_list.clear()

    @utils.thread_func("自定义RPG-初始化玩家剧情任务数据")
    def on_player_join(self, player: Player):
        self.init_player(player)
        self.try_recover_player_plot(player)

    @utils.thread_func("自定义RPG-存档玩家剧情任务数据")
    def on_player_leave(self, player: Player):
        if player in self.players_broadcast_evts_listeners:
            del self.players_broadcast_evts_listeners[player]
        if player in self.running_plot_threads:
            self.running_plot_threads[player].stop()
        if p := self.running_plots.get(player):
            self.save_player_last_plot_unend(player, p)

    def handle_plot_run(self, args):
        try:
            target, plot_name_linker = args
        except Exception:
            fmts.print_err(f"错误的剧情脚本调用: {args}")
            return
        player = self.game_ctrl.players.getPlayerByName(target)
        if player is None:
            fmts.print_war(f"{self.name}: 玩家 {target} 不存在")
        else:
            self._run_plot_by_trigger(player, plot_name_linker)

    def handle_quest_ok(self, args):
        try:
            target, quest_name = args[1:3]
        except Exception:
            fmts.print_err(f"错误的结束任务用: {args}")
            return
        quest = self.get_quest(quest_name)
        if quest is not None:
            self.finish_quest(target, quest)
        else:
            fmts.print_err(f"在 {target} 上进行了无效任务结束: {quest_name}")

    def handle_quests_menu(self, player: Player):
        quests = self.read_quests(player)
        sorted(quests, key=lambda x: x.priority, reverse=True)

        def quests_cb(_, page: int):
            if len(quests) == 0:
                return (
                    "§e§l任务列表 §6>>§r"
                    + ("\n  §8┃" + " " * 50) * 4
                    + "\n  §8┃"
                    + " " * 10
                    + "§f目前没有任何任务啦 ƪ(˘⌣˘)ʃ"
                    + ("\n  §8┃" + " " * 50) * 5
                )
            if page >= len(quests):
                return None
            output = "§e§l任务列表 §6>>§r"
            quest_datas = self.read_quest_datas(player)
            for i, quest in enumerate(quests):
                priority = quest.priority
                if priority == 3:
                    priority_color = "§6"
                elif priority == 2:
                    priority_color = "§b"
                else:
                    priority_color = "§2"
                qdata_dict = quest_datas.get(quest.tag_name, {})
                output += (
                    ("\n§b>§l §r" if i == page else "\n  ")
                    + priority_color
                    + "┃ §f§l"
                    + quest.disp_name
                    + ("    §r§7< §a抬头提交此任务" if i == page else "§r")
                    + "\n"
                    + priority_color
                    + "  ┃   §7"
                    + "\n  ┃   ".join(
                        acall(
                            quest.description,
                            player,
                            qdata_dict,
                        ).split("\n")
                    )
                    + (
                        f"； §3前往坐标 §b{acall(quest.position, player, qdata_dict)}"
                        if quest.position is not None
                        else ""
                    )
                )
            output += ("\n  §8┃" + " " * 50) * (10 - output.count("\n"))
            return output

        res = self.snowmenu.simple_select(player, quests_cb)
        if res is None:
            return False
        if res >= len(quests):
            return False
        section = quests[res]
        self.try_submit_quest(player, section)
        return True

    def place_npc_plot_cb_at(self, player: Player, _):
        _, x, y, z = player.getPos()
        x = int(x)
        y = int(y)
        z = int(z)
        resp = player.input("§6请输入超链接名：")
        if resp is None:
            player.show("§c答复超时")
            return
        rawtext = {
            "rawtext": [
                {"text": r"sr.plot.trigger"},
                {"selector": "@s"},
                {"text": resp},
            ]
        }
        self.intract.place_command_block(
            self.intract.make_packet_command_block_update(
                (x, y - 2, z + 1),
                "execute as @a[z=~-1,y=~2,r=4,c=1] run tellraw @a[tag=robot] "
                + json.dumps(rawtext, ensure_ascii=False),
                mode=1,
                need_redstone=True,
                tick_delay=2,
            ),
            facing=3,
        )
        self.intract.place_command_block(
            self.intract.make_packet_command_block_update(
                (x, y - 2, z + 2), "setblock ~~~-2 air", mode=2, conditional=True
            ),
            facing=3,
        )
        self.game_ctrl.sendcmd("tp ~~10~")
        self.rpg.show_succ(player, "命令方块放置完成")

    def place_plot_cb_at(self, player: Player, _):
        _, x, y, z = player.getPos()
        x = int(x)
        y = int(y)
        z = int(z)
        resp = player.input("§6请输入超链接名：")
        if resp is None:
            player.show("§c答复超时")
            return
        rawtext = {
            "rawtext": [
                {"text": r"sr.plot.trigger"},
                {"selector": "@s"},
                {"text": resp},
            ]
        }
        self.intract.place_command_block(
            self.intract.make_packet_command_block_update(
                (x, y, z),
                "execute as @a[r=4,c=1] run tellraw @a[tag=robot] "
                + json.dumps(rawtext, ensure_ascii=False),
                mode=0,
                need_redstone=True,
                tick_delay=2,
            )
        )
        self.rpg.show_succ(player, "命令方块放置完成")
        self.game_ctrl.sendcmd("tp ~~5~")

    def force_start_quest(self, player: Player, args):
        quest_name = args[0]
        quest = self.get_quest(quest_name)
        if quest is None:
            self.rpg.show_fail(player, "该任务不存在")
        elif plot_utils.player_is_in_quest(player, quest_name):
            self.rpg.show_fail(player, "不能重复添加任务")
        else:
            if quest in self.read_quests_finished(player):
                old = self.read_quest_datas(player)
                del old["quests_ok"][quest.tag_name]
                self.save_quest_datas(player, old)
                self.rpg.show_inf(player, "此任务之前已完成过， 重新开始任务")
            self.add_quest(player, quest)

    def force_start_quest_for_other(self, player: Player, args):
        target, quest_name = args
        target = self.game_ctrl.players.getPlayerByName(target)
        if target is None:
            self.rpg.show_fail(player, "玩家不存在")
            return
        quest = self.get_quest(quest_name)
        if quest is None:
            self.rpg.show_fail(player, "该任务不存在")
        elif plot_utils.player_is_in_quest(target, quest_name):
            self.rpg.show_fail(player, "不能重复添加任务")
        else:
            if quest in self.read_quests_finished(target):
                old = self.read_quest_datas(target)
                del old["quests_ok"][quest.tag_name]
                self.save_quest_datas(target, old)
                self.rpg.show_inf(player, "此任务之前已完成过， 重新开始任务")
            self.add_quest(target, quest)
            self.rpg.show_succ(player, "已经给此人添加任务")

    def force_finish_quest(self, player: Player, args):
        quest_name = args[0]
        quest = self.get_quest(quest_name)
        if quest is None:
            self.rpg.show_fail(player, "该任务不存在")
        elif not self.putils.player_is_in_quest(player, quest_name):
            self.rpg.show_fail(
                player,
                "当前没有这个任务： 存在任务：\n  "
                + "\n  ".join(i.tag_name for i in self.read_quests(player)),
            )
        else:
            self.finish_quest(player, quest)

    def force_remove_quest_record(self, player: Player, args):
        quest_name = args[0]
        if quest_name == "all":
            o = self.read_quest_datas(player)
            o["quests_ok"] = {}
            self.save_quest_datas(player, o)
            self.rpg.show_succ(player, "已移除所有任务记录")
            return
        quest = self.get_quest(quest_name)
        if quest is None:
            self.rpg.show_fail(player, "该任务不存在")
            return
        if not self.putils.quest_is_finished(player, quest.tag_name):
            self.rpg.show_fail(player, "该任务非已完成")
            return
        o = self.read_quest_datas(player)
        del o["quests_ok"][quest.tag_name]
        self.save_quest_datas(player, o)
        self.rpg.show_succ(player, "已移除任务记录")

    @utils.thread_func("剧情执行")
    def _run_plot_by_trigger(self, player: Player, plot_name_linker: str):
        plot = self.main_plots.get(plot_name_linker, None)
        if plot is not None:
            if (
                plot.disposable
                and self.check_plot_record(player).get(plot.tagname) is not None
            ):
                self.print(f"{player.name} 试图触发一次性剧情 {plot.tagname}, 已取消")
                return
            elif np := self.running_plots.get(player):
                fmts.print_war(
                    f"{player.name} 尝试触发剧情 {np} 但是已经在 {plot}",
                    need_log=False,
                )
                return
            plot_utils.run_plot(player, plot)
        else:
            self.rpg.show_fail(
                player, f"当前剧情关联 {plot_name_linker} 不存在， 请告知管理员"
            )

    def init_player(self, player: Player):
        self.players_broadcast_evts_listeners[player] = OnlinePlayerBroadcastListener(
            player
        )

    def init_quest_datas(self):
        return {"in_quests": [], "quests_ok": {}}

    def init_triggers_file(self):
        return []

    def regist_quest(self, quest: LegacyQuest):
        self.quests[quest.tag_name] = quest

    def read_quests(self, player: Player) -> list[LegacyQuest]:
        output = []
        for i in set(self.read_quest_datas(player)["in_quests"]):
            quest = self.get_quest(i)
            if quest:
                output.append(quest)
            else:
                self.print(f"{player.name}: 任务无效: {i}")
        return output

    def read_quests_finished(self, player: Player) -> dict[LegacyQuest, int]:
        output = {}
        for k, v in self.read_quest_datas(player)["quests_ok"].items():
            quest = self.get_quest(k)
            if quest:
                output[quest] = v
        return output

    def add_plot_record(self, player: Player, plot_name: str):
        path = self.format_plot_record_path(player)
        o = utils.tempjson.load_and_read(path, False) or {}
        o[plot_name] = int(time.time())
        utils.tempjson.load_and_write(path, o, need_file_exists=False)

    def check_plot_record(self, player: Player):
        return (
            utils.tempjson.load_and_read(self.format_plot_record_path(player), False)
            or {}
        )

    def get_quest(self, tag_name: str):
        return self.quests.get(tag_name)

    def add_quest(self, player: Player, quest: LegacyQuest):
        quests = self.read_quests(player)
        if quest in quests:
            self.rpg.show_fail(player, "§c当前任务正在进行中， 无法重复领取")
            return False
        quest_time = self.read_quests_finished(player).get(quest, None)
        if quest.cooldown is None and quest_time is not None:
            player.show(
                self.cfg["任务设置"]["任务无法提交的显示"]["任务为一次性任务"],
            )
            return False
        elif (
            quest_time is not None
            and quest.cooldown is not None
            and quest.cooldown > 0
            and time.time() - quest_time < quest.cooldown
        ):
            player.show(
                self.sec_to_timer(
                    quest.cooldown - int(time.time()) + quest_time,
                    self.cfg["任务设置"]["任务无法提交的显示"]["任务冷却"],
                ),
            )
            return False
        if quest.add_quest_cb is not None:
            ok, failed_reason = quest.add_quest_cb(player)
            if not ok:
                player.show("§c无法开始任务：")
                player.show("  " + failed_reason.replace("\n", "\n  §6"))
                return False
        o = self.read_quest_datas(player)
        self.play_quest_get_sound(player)
        self.rpg.show_any(player, "d", f"§e✦ §a接到新任务 §e{quest.disp_name}")
        self.rpg.show_any(
            player,
            "7",
            f"   {acall(quest.description, player, o.get(quest.tag_name, {}))}",
        )
        if quest.position:
            self.rpg.show_any(
                player,
                "3",
                f"§3请前往坐标 §b{acall(quest.position, player, o.get(quest.tag_name, {}))}",
            )
        o["in_quests"].append(quest.tag_name)
        self.save_quest_datas(player, o)
        self.players_broadcast_evts_listeners[player].update()
        return True

    @utils.thread_func("检查任务")
    def list_player_quests(self, player: Player):
        player_quests = self.read_quests(player)
        if not player_quests:
            self.rpg.show_fail(player, "你没有正在进行的任务")
            return
        else:
            quest_datas = self.read_quest_datas(player)
            self.rpg.show_any(player, "e", "§c➣ §e§l当前正在进行的任务：")
            for i, quest in enumerate(player_quests):
                if quest is None:
                    self.rpg.show_any(player, "f", f"{i + 1}： §c<任务失效>\n")
                else:
                    self.rpg.show_any(
                        player,
                        "f",
                        f"{i + 1}： {quest.disp_name}\n§7┃   {acall(quest.description, player, quest_datas.get(quest.tag_name, {}))}",
                    )
            self.rpg.show_inf(player, "在聊天栏输入任务序号以提交任务：")
            resp = player.input()
            if resp is None:
                return
            resp = utils.try_int(resp.strip("[]"))
            if resp is None:
                player.show("§c序号不合法")
                return
            if resp not in range(1, len(player_quests) + 1):
                self.rpg.show_fail(player, "序号超出范围")
                return
            getting_quest = player_quests[resp - 1]
            if getting_quest is None:
                self.rpg.show_fail(player, "无法完成失效的任务")
                return
            self.try_submit_quest(player, getting_quest)

    def try_submit_quest(self, player: Player, quest: LegacyQuest):
        if quest.detect_cb:
            with QuestDataMaintainer(player, quest, readonly=True) as m:
                ok, failed_reason = quest.detect_cb(player, m.data)
                if failed_reason == "":
                    failed_reason = "条件未达成"
        else:
            self.rpg.show_fail(player, "§c该任务不能手动提交")
            return
        if not ok:
            player.show(self.cfg["任务设置"]["任务无法提交的显示"]["显示头"])
            player.show("  " + failed_reason.replace("\n", "\n§6  "))
            return
        else:
            self.finish_quest(player, quest)

    def finish_quest(self, player: Player, quest: LegacyQuest):
        quest_datas = self.read_quest_datas(player)
        if quest.tag_name not in quest_datas["in_quests"]:
            self.rpg.show_fail(player, f"你没有接到该任务： {quest.tag_name}")
            return
        if quest.tag_name in quest_datas:
            del quest_datas[quest.tag_name]
        quest_datas["quests_ok"][quest.tag_name] = int(time.time())
        quest_datas["in_quests"].remove(quest.tag_name)
        self.play_quest_finished_sound(player)
        with QuestDataMaintainer(player, quest, readonly=True) as m:
            for cmd in self.cfg["任务设置"]["任务完成执行的指令"]:
                self.game_ctrl.sendwocmd(
                    utils.simple_fmt(
                        {
                            "[玩家名]": player.name,
                            "[任务名]": quest.disp_name,
                            "[任务描述]": acall(
                                quest.description,
                                player,
                                quest_datas.get(quest.tag_name, m.data),
                            ),
                        },
                        cmd,
                    )
                )
        if quest.finish_cb:
            with QuestDataMaintainer(player, quest, readonly=True) as m:
                quest.finish_cb(player, m.data)
        if quest.tag_name in quest_datas:
            del quest_datas[quest.tag_name]
        self.save_quest_datas(player, quest_datas)
        self.players_broadcast_evts_listeners[player].update()
        self.tutor.check_point("自定义RPG-剧情与任务:完成任务", player, quest)

    def create_plotskip_detector(self, player: Player):
        return PlotSkipDetector(self, player)

    def handle_snowball_blocking(self, dats: list[str]):
        player = dats[0]
        if player in self.snowball_blocking_handler.keys():
            self.snowball_blocking_handler[player] = True
            return True
        return False

    def try_recover_player_plot(self, player: Player):
        if p := self.get_player_last_plot_position(player):
            pos_str = " ".join(map(str, p[1:]))
            self.game_ctrl.sendwocmd(f"tp {player.safe_name} {pos_str}")
            self.rpg.show_warn(player, "你的剧情播放被中断， 进度已重置")
            self.save_player_last_plot_position(player, None)
            self.game_ctrl.sendwocmd(f"effect {player.safe_name} blindness 0 0")
            plot_utils.enable_movement(player)
        if p := self.get_player_last_plot_unend(player):
            self.rpg.show_warn(player, "恢复退出游戏时播放的剧情")
            self.save_player_last_plot_unend(player, None)
            plot_utils.run_plot(player, p)

    @staticmethod
    def sec_to_timer(timesec: int, fmt: str):
        days, left = divmod(timesec, 86400)
        hrs, left = divmod(left, 3600)
        mins, secs = divmod(left, 60)
        if secs > 0 and mins == 0:
            mins = 1
        return utils.simple_fmt({"%d": days, "%H": hrs, "%M": mins, "%S": secs}, fmt)

    @staticmethod
    def format_timer_zhcn(timemin: int):
        fmt_string = ""
        if timemin >= 1440:
            days = timemin // 1440
            fmt_string += f"{days}天"
        if timemin >= 60 and timemin % 1440:
            hrs = timemin // 60 - (timemin // 1440 * 1440) // 60
            fmt_string += f"{hrs}小时"
        if timemin % 60:
            fmt_string += f"{timemin % 60}分钟"
        return fmt_string

    @utils.thread_func("任务接取音效")
    def play_quest_get_sound(self, player: Player):
        for vol in range(4, 0, -1):
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 2.8'
            )
            time.sleep(0.1)
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 3.2'
            )
            time.sleep(0.1)
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 4.2'
            )
            time.sleep(0.1)

    @utils.thread_func("任务完成音效")
    def play_quest_finished_sound(self, player: Player):
        for vol in range(4, 0, -1):
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 2.8'
            )
            time.sleep(0.1)
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 3.6'
            )
            time.sleep(0.1)
            self.game_ctrl.sendwocmd(
                f'execute as @a[name="{player.name}"] at @s run playsound note.bit @s ~~~ {vol / 4} 5.6'
            )
            time.sleep(0.1)

    def broadcast_listener(self, b: InternalBroadcast):
        for _, bc in self.players_broadcast_evts_listeners.items():
            bc.active(b.evt_name, b.data)

    def format_general_data_path(self, player: Player):
        return self.data_path / DATA_PATH / (player.xuid + ".json")

    def format_quest_data_path(self, player: Player):
        return self.data_path / QUEST_DATA_PATH / (player.xuid + ".json")

    def format_plot_record_path(self, player: Player):
        return self.data_path / PLOT_REC_PATH / (player.xuid + ".json")

    def format_shop_cd_path(self, player: Player):
        return self.data_path / SHOP_CD_PATH / (player.xuid + ".json")

    def format_plot_point_data_path(self, player: Player):
        return self.data_path / PLOT_POINT_DATA / (player.xuid + ".json")

    def read_quest_datas(self, player: Player):
        return utils.tempjson.load_and_read(
            self.format_quest_data_path(player),
            need_file_exists=False,
            default=self.init_quest_datas,
        )

    def save_quest_datas(self, player: Player, data: dict):
        utils.tempjson.load_and_write(
            self.format_quest_data_path(player), data, need_file_exists=False
        )

    def get_player_last_plot_position(
        self, player: Player
    ) -> tuple[int, int, int, int] | None:
        data = self.read_quest_datas(player).get("last_plot_position", None)
        return tuple(data) if data else None

    def save_player_last_plot_position(
        self, player: Player, pos: tuple[int, int, int, int] | None
    ):
        data = self.read_quest_datas(player)
        data["last_plot_position"] = list(pos) if pos else None
        self.save_quest_datas(player, data)

    def get_player_last_plot_unend(self, player: Player):
        data = self.read_quest_datas(player).get("last_plot_unend", None)
        if data is None:
            return None
        return self.plots.get(data, None)

    def save_player_last_plot_unend(
        self, player: Player, plot: quest_loader.RegisteredPlot | None
    ):
        data = self.read_quest_datas(player)
        data["last_plot_unend"] = plot.raw_name if plot else None
        self.save_quest_datas(player, data)

    # 设置玩家在某个商店的物品剩余购买次数和商品刷新的冷却时间
    def set_shop_left2cddata(
        self,
        player: Player,
        shop_name: str,
        tag: str,
        left: int,
        cdmin: int,
    ):
        path = self.format_shop_cd_path(player)
        f = utils.tempjson.load_and_read(path, default={})
        f.setdefault(shop_name, {})
        oldcd, _ = f.setdefault(shop_name, {}).get(tag, (0, 0))
        cdmin_till_now = int(oldcd - time.time() // 60)
        # BUG
        if cdmin_till_now > 0:
            cdmin = cdmin_till_now
        cdmin_time = int(time.time() // 60 + cdmin)
        f[shop_name][tag] = [left, cdmin_time]
        utils.tempjson.load_and_write(path, f, False)
        utils.tempjson.flush(path)

    def get_shop_left2cd(
        self,
        player: Player,
        shop_name: str,
        tag: str,
    ) -> tuple[int, int]:
        f = utils.tempjson.load_and_read(
            self.format_shop_cd_path(player), False, default={}
        )
        lft, cd = f.setdefault(shop_name, {}).get(tag, (None, 0))
        return lft, max(cd - time.time() // 60, 0)

    def set_state(self, player: Player, name: str, state: bool):
        path = self.format_general_data_path(player)
        o = utils.tempjson.load_and_read(path, need_file_exists=False, default={})
        o.setdefault("states", {})
        if state:
            o["states"][name] = state
        elif o["states"].get(name):
            del o["states"][name]
        utils.tempjson.load_and_write(path, o, need_file_exists=False)

    def get_state(self, player: Player, name: str):
        path = self.format_general_data_path(player)
        o = utils.tempjson.load_and_read(path, need_file_exists=False, default={})
        o.setdefault("states", {})
        return bool(o["states"].get(name))

    def get_quest_point_datas(self, player: Player):
        path = self.format_general_data_path(player)
        o = utils.tempjson.load_and_read(path, need_file_exists=False, default={})
        return o

    def save_quest_point_datas(self, player: Player, data: dict):
        path = self.format_general_data_path(player)
        utils.tempjson.load_and_write(path, data, need_file_exists=False)

    def get_quest_point_data(self, player: Player, quest_linkname: str):
        return self.get_quest_point_datas(player).get(quest_linkname, {})

    def set_quest_point_data(self, player: Player, quest_linkname: str, data: dict):
        old = self.get_quest_point_datas(player)
        old[quest_linkname] = data
        self.save_quest_point_datas(player, old)
        
    def player_in_plot(self, player: Player):
        return self.running_plots.get(player, None)

    # Only can used by bq_loader
    def _regist_plot(self, plot: quest_loader.RegisteredPlot):
        self.plots[plot.raw_name] = plot

    # Only can used by bq_loader
    def _regist_main_plot(self, plot: quest_loader.RegisteredPlot):
        self.main_plots[plot.linked_to] = plot

    # Only can used by bq_loader
    def _add_plot_insertion(self, plot: quest_loader.RegisteredPlot):
        self.inserted_plots.setdefault(plot.linked_to, []).append(plot)

    # Only can used by bq_loader
    def _add_plot_choice_insertion(self, plot: quest_loader.RegisteredPlot):
        section_text = plot._section_text
        if section_text is None:
            raise ValueError("not a section insertion plot")
        old = self.choicable_inserted_plots.setdefault(plot.linked_to, [])
        if plot.pfunc.__name__ in (p.pfunc.__name__ for p in old):
            raise Exception(f"§6重复插入剧情: {plot}")
        old.append(plot)

    # Only can used by bq_loader
    def _get_insertions(self, linkto: str):
        return self.inserted_plots.get(linkto, [])

    # Only can used by bq_loader
    def _get_choicable_insertions(self, linkto: str):
        return self.choicable_inserted_plots.get(linkto, [])


entry = plugin_entry(CustomRPGPlotAndTask, "自定义RPG-剧情与任务")
plot_utils.set_system(entry)
quest_loader.set_system(entry)
